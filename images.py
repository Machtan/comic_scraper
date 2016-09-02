# coding: utf-8
# Created by Jabok @ August 17th 2014
# images.py
"""
Responsible for the correct finding, identifying and testing of comic images
"""
import os, tempfile, imghdr, shutil, sys
import urllib.parse
from urllib.parse import urljoin, urlparse
from finder import isimage, findcommonidentifiers, _getter, Identifier
from bs4 import BeautifulSoup
from PIL import Image

def imagesize(path):
    #print("Finding the size of path:", path)
    
    try:
        return Image.open(path).size
    except Exception as e:
        print(e)
        print("Unknown image format in image: '{0}'".format(path))
        fname = "errfile_"+os.path.basename(path)
        fpath = os.path.join(os.getcwd(), fname)
        shutil.copy(path, fpath)
        print("Copied failed image to '{0}'".format(fpath))
        return (0, 0)

# - - - Soup filters 
def isheader(tag):
    """Soup header identifier"""
    return tag.name == "header"

def withname(name):
    def identify(tag):
        return tag.name == name
    return identify

imagetypes = set([ # TODO have I forgotten anything?
    "png",
    "jpg",
    "jpeg",
    "gif"
])
def isvalidimage(tag):
    if isimage(tag):
        path = urlparse(tag['src']).path
        ending = path.split(".")[-1]
        return (not tag.find_parent(isheader)) and (ending in imagetypes)
    return False    

# - - - Other functions
def getlocal(*path):
    return os.path.join(os.path.dirname(__file__), os.path.join(*path))
    
def findimages(soup, page, identifier):
    """Finds the images identified by the given identifier in the soup,
    and returns their source urls"""
    found = identifier.identify(soup)
    urls = set()
    if not found:
        print("Could not find any images using {0}!".format(identifier))
    for image in found:
        urls.add(image['src'])
    return [urljoin(page, url) for url in urls]  

def validateidentifiers(tag, identifiers, firstsoup, nextsoup, validimages):
    """Checks and finds the valid identifiers for the given tag in the soup,
    then checks whether it works for the second as well."""
    validimages = set(validimages)
    
    print("Validating identifiers:")
    for identifier in identifiers:
        print("-", identifier)
    
    # Find out which identifiers work
    valid = []
    for identifier in identifiers: 
        found = identifier.identify(firstsoup)
        isvalid = True
        for image in found:
            #print("- Found {0}".format(image['src']))
            if not image in validimages:
                isvalid = False # Nope, this won't do
        if isvalid:
            valid.append(identifier)
    
    # Prove that these identifiers work on the second page as well
    proven = []
    print("Valid identifiers:")
    for identifier in valid:
        found = identifier.identify(nextsoup)
        print("-", identifier, "->")
        for tag in found:
            print("---", tag['src'])
        if found:
            proven.append(identifier)
    
    return proven

def findimageidentifiers(tag, soup):
    """Finds the ways to identify the given image tag in the soup"""
    identifiers = []
    # 1) Check common identifiers
    identifiers += findcommonidentifiers(tag, soup)
    
    # 2) Check parent identifiers
    for parent in tag.find_parents():
        pids = findcommonidentifiers(parent, soup)
        if pids:
            identifiers.append(Identifier(tag.name, "parent", pids=pids))
    
    return identifiers

def findlargerthan(imagetags, minsize, page):
    """Returns the given image tags that are larger than the size, or
    if none are, the largest of them."""
    # Image sorting function
    def bysize(args):
        imgsize = args[1]
        return imgsize[0] * imgsize[1]
    
    with tempfile.TemporaryDirectory() as folder: # clean!
        print("Folder:", folder)
        imageinfo = [] # (imagetag, size, path)
        for num, image in enumerate(imagetags):
            src = image['src']
            if os.path.exists(getlocal(src)): # It's a local file
                path = src
            else: # Fetch
                url = urljoin(page, src)
                data = _getter.get_read(url, reconnect=True)
                if not data:
                    raise Exception("No image data read from url '{0}'!".format(url))
                ending = imghdr.what(None, data)
                if not ending:
                    ending = urlparse(url).path.split(".")[-1]
                    print("Could not determine image format using imghdr, ")
                    print("found '{0}' by parsing the url".format(ending))
                fname = "{0}.{1}".format(num, ending)
                path = os.path.join(folder, fname)
                with open(path, "wb") as f: # Save the image
                    f.write(data)
            # Check the image
            imgsize = imagesize(path)
            imageinfo.append((image, imgsize, path))
        
        larger = []
        print("Larger images:")
        for (tag, imgsize, path) in imageinfo:
            if (imgsize[0] >= minsize[0]) and (imgsize[1] >= minsize[1]):
                print("{0}: {1}".format(imgsize, tag['src']))
                larger.append(tag)
        if not larger:
            print("No images larger than {0} was found!".format(minsize))
            print("Finding the largest image...")
            # Try and find the larger of the small ones
            largest = sorted(imageinfo, key=bysize)[-1]
            print("Largest:", largest)
            larger.append(largest[0])
            
    return larger

def findimagefinder(firstpage, nextpage, minsize=(350, 350),
    silent=False):
    """Finds the images in the pages and a way of identifying them"""
    try:
        p1 = _getter.get_read(firstpage)
        startsoup = BeautifulSoup(p1)
        p2 = _getter.get_read(nextpage)
        nextsoup = BeautifulSoup(p2)
    except Exception as e:
        raise e
    
    images = startsoup.find_all(isvalidimage)
    # Find all the images bigger than or equal to the size
    print("Finding larger images....")
    larger = findlargerthan(images, minsize, firstpage)
    print("Found!")
    
    valid = []
    # Now find out how to identify them
    for imagetag in larger:
        print("Finding identifier for '{0}'".format(imagetag['src']))
        identifiers = findimageidentifiers(imagetag, startsoup)
        proven = validateidentifiers(imagetag, identifiers, startsoup,
            nextsoup, set(larger))
        if proven:
            print("- Proven:")
            for iid in proven:
                print("---", iid)
            valid.append(proven[0])
        else:
            print("No proven identifiers found :(")
    if not valid:
        raise Exception("No proven image identifiers found!")
    return valid[0]