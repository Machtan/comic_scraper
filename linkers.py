# coding: utf-8
# Created by Jabok @ August 17th 2014
# linkers.py
"""
Finds and tests identifiers for a link connection between comic pages
"""
import urllib.parse
from urllib.parse import urljoin
from finder import findcommonidentifiers, isimage, _getter, Identifier
from utils import printiter
from bs4 import BeautifulSoup

# - - - Soup filters 
def isnextlink(firstpage, nextpage):
    """Function generator for a soup tag identifier for the link to the next 
    page from the first"""
    def identify(tag):
        if tag.has_attr("href"):
            if urljoin(firstpage, tag['href']) == nextpage:
                return True
        return False
    return identify

# - - - Other functions
def workinglinkers(firstsoup, nextsoup, tag, identifiers, validtags):
    """Tests the identifiers found for the tag in the soup of the next page,
    returning any identifiers that work"""
    validtags = set(validtags)
    working = []
    name = tag.name
    for identifier in identifiers:
        foundfirst  = identifier.identify(firstsoup)
        foundsecond = identifier.identify(nextsoup)
        valid = True
        for linktag in foundfirst:
            if not linktag in validtags:
                valid = False
        # Works on both pages and no false positives
        if valid and foundfirst and foundsecond: 
            working.append(identifier)
    return working

def findlink(soup, page, identifier):
    """Finds a link identified by the identifier in the given soup.
    The identifier should be [tagname, [checkfunc, [*args]]]"""
    found = identifier.identify(soup)
    if not found:
        print("Could not find any link using {0}!".format(identifier))
    return urljoin(page, found[0]['href']) if found else None

def findlinkers(tag, soup):
    """Finds the best way to identify the given linker tag in the soup"""
    identifiers = [] # (checkfunc, (*args))
    name = tag.name
    
    # 1) Check common identifiers
    identifiers += findcommonidentifiers(tag, soup)
    
    # 2) Check whether the text makes sense to use
    if tag.text:
        identifiers.append(Identifier(name, "member", mem="text", val=tag.text))
    
    # 3) Check whether it's an image that can be used
    if tag.has_attr('src'):
        identifiers.append(Identifier(name, "attribute", attr='src', val=tag['src']))
    
    # 4) Check whether it contains an image that can be used
    images = tag.find_all(isimage)
    if images:
        for image in images:
            identifiers.append(Identifier(name, "sub-image", val=image['src']))
    
    return identifiers    

def findlinker(firstpage, nextpage, silent=False):
    """Finds a working linker identifier to go from the first page to the next"""
    def debug(*args, **kwargs):
        if not silent: print(*args, **kwargs)
    def debugiter(*args, **kwargs):
        if not silent: printiter(*args, **kwargs)
    
    try:
        p1 = _getter.get_read(firstpage)
        firstsoup = BeautifulSoup(p1)
        p2 = _getter.get_read(nextpage)
        nextsoup = BeautifulSoup(p2)
        #print("firstsoup:", firstsoup)
    except Exception as e:
        raise e
    
    debug("- Identifying next link...")
    links = firstsoup.find_all(isnextlink(firstpage, nextpage))
    debug("Found links:")
    for num, link in enumerate(links):
        debug("--", num, "--")
        debug(link)
        pass
    
    debug("Identifiers:")
    identifiers = []
    for num, linktag in enumerate(links):
        debug("- Linker tag #{0} --".format(num))
        identifiers.append(findlinkers(linktag, firstsoup))
        debugiter(identifiers[num])
    
    debug("Working:")
    linkers = []
    for num, linktag in enumerate(links):
        linkers += workinglinkers(firstsoup, nextsoup, linktag, identifiers[num], links)
    
    if not linkers:
        raise Exception("No working linkers found!")
    return linkers[0] # Perhaps give some more :)? 
    # (it's not like it'll bloat (probably))