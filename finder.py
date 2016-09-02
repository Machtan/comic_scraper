# coding: utf-8
# Created by Jabok @ August 14th 2014
# finder.py
"""
Gneral finding methods and testing
"""
from bs4 import BeautifulSoup
from getter import Getter
from utils import printiter
import toml
_getter = Getter(timeout=5)

def isimage(tag):
    """Soup image identifier"""
    return tag.name == "img"

# Link checking functions
def attrcheck(attr, val):
    """Generates a soup identification function that checks whether
    the given attribute of the tag is the given value."""
    def identify(tag):
        if tag.has_attr(attr):
            return tag[attr] == val
        return False
    return identify

def memcheck(mem, val):
    """Same as above, but with members"""
    def identify(tag):
        if hasattr(tag, mem):
            return getattr(tag, mem) == val
        return False
    return identify

def subimgcheck(val):
    """Identifier for a tag with the given image child"""
    def identify(tag):
        for image in tag.find_all(isimage):
            if image['src'] == val:
                return True
        return False
    return identify

def parcheck(pids):
    """Checks for a tag with the given type, that has a parent fulfilling
    the list of checks"""
    def identifyparent(tag):
        for identifier in pids:
            if identifier.validate(tag):
                return True
        return False
        
    def identify(tag):
        if tag.find_parent(identifyparent):
            return True
        else:
            return False
    return identify

checkfuncs = {
    "attribute": attrcheck,
    "member": memcheck,
    "sub-image": subimgcheck,
    "parent": parcheck
}

class Identifier:
    """A simpler way of identifying tags"""
    def __init__(self, tagname, func, **kwargs):
        if not func in checkfuncs:
            raise Exception("Invalid function '{0}'!".format(func))
        self.name   = tagname
        self.func   = func
        self.kwargs = kwargs
        self.check  = checkfuncs[func](**kwargs)
        
    def getdict(self):
        """Serialize to a simple-type dictionary"""
        d = {"name": self.name, "func": self.func}
        kwargs = {}
        for key, val in self.kwargs.items(): # Format identifier arguments (mainly parent stuff)
            if key == "pids": #EXCEPTION
                kwargs[key] = [pid.getdict() for pid in val]
            else:
                kwargs[key] = val
        d['kwargs'] = kwargs
        return d
    
    def load(data):
        """Deserialize from a dictionary"""
        kwargs = {}
        for key, val in data['kwargs'].items():
            if key == "pids": #EXCEPTION again
                kwargs[key] = [Identifier.load(pid) for pid in val]
            else:
                kwargs[key] = val
        return Identifier(data['name'], data['func'], **kwargs)
    
    def validate(self, tag):
        return self.check(tag) and (tag.name == self.name)
    
    def identify(self, soup):
        """Identifies tags of the type in the soup"""
        return list(soup.find_all(self.validate))
    
    def __str__(self):
        return "[{0}:{1}(**{2})]".format(self.name, self.func, self.kwargs)
    
    def __repr__(self): 
        return str(self)

def findcommonidentifiers(tag, soup):
    """Finds the common (between links and images) identifiers of the tag"""
    # 1) Check whether the class, id or rel makes sense to use
    identifiers = []
    name = tag.name
    if tag.has_attr('class'):
        identifiers.append(Identifier(name, "attribute", attr="class", val=tag['class']))
    if tag.has_attr('id'):
        identifiers.append(Identifier(name, "attribute", attr="id", val=tag['id']))
    if tag.has_attr('rel'):
        identifiers.append(Identifier(name, "attribute", attr='rel', val=tag['rel']))
    return identifiers