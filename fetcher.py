# coding: utf-8
# Created by Jabok @ August 14th 2014
# fetcher.py
import os
import toml
from validators import validate_specs
from comic import Comic
from linkers import findlink
from images import findimages
from getter import Getter
from finder import Identifier
from bs4 import BeautifulSoup
from utils import lastcomicfile
"""
Initiates the fetching of a comic, attempting to generate the schema if necessary.
"""
_getter = Getter(timeout=5)

def findcontent(url, link_identifier, progress_identifier):
    """Finds image url and the link to the next page at the given web address."""
    # Url should be a full url path for correct url joining!
    image, nextpage = None, None
    soup = BeautifulSoup(_getter.get(url))
    nextpage = findlink(soup, url, link_identifier)
    if not (image and newpage): raise Exception("Nothing Found!")
    return image, nextpage        

def fetchcomic(request, overwrite=False, startpage=None, 
    pages=-1):
    """Fetches the comic described in the given request"""
    from utils import getcomiclist, printiter
    # If it is not a comic name that is known
    if os.path.exists(request):
        with open(request) as f:
            specs = toml.load(f)
        title = specs['title']
        directory = os.path.dirname(request) or os.getcwd()
    else:
        title = request.strip()
        directory = os.getcwd()
    
    if (not title in getcomiclist()) or overwrite:
        if not os.path.exists(request):
            return print("Could not find any specfile or comic '{0}'!".format(request))
        
        # Validate the given specification
        print("Validating... ", end="")
        valid, errors = validate_specs(specs, directory=directory)
        print("OK" if valid else "FAILED")
        if not valid:
            print("Cannot fetch a comic from the given spec due to the following errors:")
            return printiter(errors)
            
        Comic.create(specs, directory=directory)
        
    print("Preparing scrape...")
    with Comic.load(title) as comic:
        print("- Comic:", comic)
        link_identifier     = Identifier.load(comic.progress['link_identifier'])
        image_identifier    = Identifier.load(comic.progress['image_identifier'])
        
        lastimages  = comic.progress['lastimages'] 
        remaining   = pages
        reconnect   = comic.progress.get('reconnect', False)
        lastpage    = comic.progress['lastpage']
        if (not lastpage) or startpage: # No previous, or start supplied
            nextpage = startpage or specs['startpage']
            print("- Starting new scrape from", nextpage)
        else:
            print("- Resuming scrape from", lastpage)
            data        = _getter.get_read(lastpage)
            soup        = BeautifulSoup(data)
            nextpage    = findlink(soup, lastpage, link_identifier)
        
        # Do the actual scraping
        try:
            if nextpage: 
                pagestamp = "({0} pages)".format(pages) if (pages != -1) else ""
                print("Starting scrape..."+pagestamp)
            
            while nextpage and remaining: # There is a way!
                print("- {0:03}: {1}".format(comic.progress['lastindex']+1, nextpage))
                data        = _getter.get_read(nextpage, reconnect=reconnect)
                soup        = BeautifulSoup(data)
                imageurls   = findimages(soup, nextpage, image_identifier)
                if not imageurls:
                    print("No images found at '{0}'! Ending...".format(nextpage))
                    break
                if imageurls == lastimages:
                    print("Image duplicates found at '{0}'! Ending...".format(nextpage))
                    break
                for url in imageurls:
                    comic.add(url, reconnect=reconnect)
                comic.setscraped(nextpage, imageurls)
                lastimages  = imageurls # Don't repeat content!
                lastpage    = nextpage
                nextpage    = findlink(soup, nextpage, link_identifier)
                if nextpage == lastpage:
                    print("No further links found at '{0}'! Ending...".format(lastpage))
                    break
                remaining  -= 1
            lastpage = comic.progress['lastpage']
            print("No more comics found after '{0}', ending...".format(lastpage))
        except KeyboardInterrupt:
            print("\nInterrupted!")
            print("Progress:")
            print("- Last page: ", comic.progress['lastpage'])
            print("- Last index:", comic.progress['lastindex'])
            print("Closing...", end=" ")
        except Exception as e:
            print("CAUGHT EXCEPTION!")
            print("Closing...", end=" ")
            raise
    
    meta = {"lastcomic": title}
    with open(lastcomicfile, "w") as f:
        toml.dump(meta, f)
    print("Scrape ended.")