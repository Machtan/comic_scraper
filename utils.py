# coding: utf-8
# Created by Jabok @ August 14th 2014
# utils.py
import os, sys, subprocess, toml
from ziparchive import ZipArchive
from validators import validate_metadata, validate_progdata
from argparse import ArgumentParser
"""
Holds the various utility functions for the comic scraper, along
with some of the harder-to-classify program functions.
"""

def getlocal(*path):
    """Returns the path relatively to this script's location"""
    return os.path.join(os.path.dirname(__file__), os.path.join(*path))

def printiter(iterable):
    """Prints the elements of the given iterable a little more prettily"""
    for e in iterable:
        print("-", e)

def ensure(directory):
    """Creates the given directory if it does not exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)
    
def assertpath(path, filetype="path"):
    """Asserts that the given path exists"""
    if not os.path.exists(path):
        print("The {1} '{0}' does not exist!".format(path, filetype))
        return False
    return True

# Global tweakable variables
comicdir        = getlocal("comics")
metadir         = getlocal("metadata")
metadatafile    = ".metadata.toml" # inside the zip
progressfile    = ".progress.toml"
defaultarchive  = ZipArchive
extension       = ".cbz"
lastcomicfile   = os.path.join(metadir, "lastcomic.toml")

"""
Needed interface for archives
create(filepath)
load(filepath, mode='r')
write(self, member, content)
read(self, member)
remove(self, member)
close(self)
list(self)
__enter__(self)
__exit__(self)
"""
def read(*args):
    """read [comic]
    Opens the comic with the given title for reading."""
    from __main__ import printhelp
    if not args:
        return printhelp("read")
    name = " ".join(args).strip()
    title = None
    if name in getcomiclist():
        title = name
    else:
        for comic in getcomiclist():
            if comic.startswith(name):
                title = comic
                break
    if title:
        print("Opening '{0}'...".format(title))
        path = os.path.join(comicdir, title+extension)
        if "darwin" in sys.platform:
            subprocess.Popen(["open", "-a", "Simple Comic", path])
        else:
            subprocess.Popen(["open", path])
    else:
        print("No comic found.")

def getcomiclist():
    """Returns a list of the names of the comics currently in local storage"""
    comics = []
    if os.path.exists(comicdir): 
        for file in os.listdir(comicdir):
            if file.endswith(extension):
                comics.append(file[:-1*len(extension)])
    return sorted(comics)

def listcomics(*args):
    """list [prefix]
    Lists the locally stored comics (optionally starting with 
    the given text)."""
    prefix  = " ".join(args).strip()
    valid   = [comic for comic in getcomiclist() if comic.startswith(prefix)]
    if not valid:
        print("No comics present!")
    else:
        for comic in valid:
            print("-", comic)
        if (len(valid) == 1) and "darwin" in sys.platform:
            with subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE) as proc:
                text = '"{0}"'.format(valid[0])
                subprocess.Popen(["echo", text], stdout=proc.stdin)
                print("> Copied comic to clipboard ;)")

def infocomic(*args):
    """info [comic]
    Prints more information about a scraped comic."""
    from __main__ import printhelp
    if not args:
        return printhelp("info")
    query = " ".join(args).strip()

def resume(*args):
    """resume
    Resumes the scraping of the most recently scraped comic."""
    from fetcher import fetchcomic
    if not os.path.exists(lastcomicfile):
        print("No previous scraping data found.")
    else:
        with open(lastcomicfile) as f:
            info = toml.load(f)
            specfile = info['lastcomic']
            directory = os.path.dirname(specfile) or os.getcwd()
            with open(specfile) as s:
                specs = toml.load(s)
                print("Resuming scrape of comic", specs['title'])
                fetchcomic(specs, directory=directory)

def edit(*args):
    """Moves and opens the medadata (or progress) of a comic for editing"""
    from __main__ import _editcmd
    desc = "Moves and opens the medadata of a comic for editing"
    prog = os.path.basename(sys.argv[0])+" "+_editcmd
    parser = ArgumentParser(description=desc, prog=prog)
    parser.add_argument("comic", 
        help="The comic whose metadata to edit")
    parser.add_argument("-p", "--edit_progress_data", action="store_true",
        default=False, 
        help="Whether the progress data should be edited instead")
    args = parser.parse_args(args)
    editprog = args.edit_progress_data
    affix = "prog" if editprog else "meta"
    
    from comic import Comic
    title = args.comic
    comic = Comic.load(title)
    ensure(metadir)
    target = os.path.join(metadir, title+"_"+affix+".toml")
    if not os.path.exists(target): # use the existing one if possible
        with open(target, "w") as w:
            if editprog:
                toml.dump(comic.progress, w)
            else:
                toml.dump(comic.metadata, w)
    else:
        print("- Found existing patch file")
    print("The file is now available at '{0}'".format(target))
    print("Use <{0} patch '{1}'> to apply the changes".format(sys.argv[0], title))
    
    # TODO improve this, yes?
    if "darwin" in sys.platform:
        subprocess.Popen(["open", "-a", "TextMate", target])
    
def patch(*args):
    """patch
    Patches the metadata of a comic edited with 'edit' into it"""
    from comic import Comic
    from __main__ import printhelp
    if not args:
        return printhelp("patch")
    title = " ".join(args).strip()
    print("Patching '{0}'...".format(title))
    
    # Look for an edited metadata file in the folder for those :)
    metapath = os.path.join(metadir, title+"_meta.toml")
    progpath = os.path.join(metadir, title+"_prog.toml")    
    
    with Comic.load(title) as comic:
    # Validate the metadata file
        if os.path.exists(metapath):
            with open(metapath) as f:
                metadict = toml.load(f)
            valid, errors = validate_metadata(metadict)
            if not valid:
                print("Could not patch the metadata due to the following errors:")
                return printiter(errors)
            else:
                print("- Patching metadata...")
                comic.metadata = metadict
                os.remove(metapath)
                
        if os.path.exists(progpath):
            with open(progpath) as f:
                progdict = toml.load(f)
            valid, errors = validate_progdata(progdict)
            if not valid:
                print("Could not patch the metadata due to the following errors:")
                return printiter(errors)
            else:
                print("- Patching progress data...")
                comic.progress = progdict
                os.remove(progpath)
    
    print("Done!")