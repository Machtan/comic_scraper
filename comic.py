# coding: utf-8
# Created by Jabok @ August 14th 2014
# comic.py
import os, toml, imghdr, tempfile, sys
from getter import Getter
from utils import defaultarchive, comicdir, progressfile, metadatafile, extension # vars
from utils import assertpath # funcs
from linkers import findlinker
from images import findimagefinder

"""
Holds the comic class and its utilities
"""

_getter = Getter(timeout=5)
class Comic:
    """Convenience class for the representation of a comic"""
    def __init__(self, archive, progress, metadata):
        self.archive    = archive
        self.progress   = progress
        self.metadata   = metadata
        
        # If the scraper breaks halway through scraping a page with multiple images
        self.unsavedindex   = progress['lastindex']
        #self.unsavedimages  = []
    
    def add(self, imageurl, reconnect=False):
        """Adds an image with the given url to the comic"""
        index       = self.progress['lastindex'] + 1
        imgbytes    = _getter.get_read(imageurl, reconnect=reconnect)
        ending      = imghdr.what(None, imgbytes)
        fname       = "image{0}.{1}".format(str(index), ending)

        self.archive.write(fname, imgbytes)
        self.unsavedindex = index
        #self.unsavedimages.append(fname)
    
    def setscraped(self, page, images):
        """Sets the last fetched page of the comic to the given one"""
        self.progress['lastpage']   = page
        self.progress['lastimages'] = images
        self.progress['lastindex']  = self.unsavedindex
        #self.unsavedimages          = [] # clear
    
    def __enter__(self): # Support context management
        return self
    
    def __exit__(self, *errargs):
        # Write changes to metadata and progress
        with tempfile.TemporaryFile(mode="w") as f: # Act responsibly: No evidence
            out = sys.stderr
            sys.stderr = f
            self.archive.write(metadatafile, toml.dumps(self.metadata))
            self.archive.write(progressfile, toml.dumps(self.progress))
            sys.stderr = out
        self.archive.close() # Clean up
    
    def create(specs, directory=None):
        """Creates a new comic with the given name and specification dictionary,
        using the given working directory for relative file paths."""
        print("Creating comic in directory", directory)
        directory = directory if directory else os.getcwd()
        if not os.path.exists(comicdir):
            os.makedirs(os.path.join(os.path.dirname(__file__), comicdir))
        def localpath(path):
            return os.path.join(directory, path)    
        
        title = specs['title']
        print("Creating comic '{0}'... ".format(title))
        print("- Copying metadata")
        archivepath = os.path.join(comicdir, title+extension)
        if os.path.exists(archivepath):
            print("- Removing old archive")
            os.remove(archivepath)
        
        archive =  defaultarchive.create(archivepath)
        # Copy metadata over
        def copypath(member, target):
            if member in specs:
                source = specs[member]
                with open(source, "rb") as f:
                    reps = {"ext": source.split(".")[-1]}
                    archive.write(target.format_map(reps), f.read())
            
        copypath("descriptionfile", ".description.{ext}") # After the images
        copypath("coverfile", "cover.{ext}")
        metadata = specs.copy()
        for member in ["descriptionfile", "coverfile"]:
            metadata.pop(member, None) # Lazy pop
        archive.write(metadatafile, toml.dumps(metadata))
        
        # Generate the progress stuff here
        progress = {
            'lastindex': 0, # Start indexing at one(ce)!
            'lastimages': [],
            'lastpage': ""
        }
        
        print("- Generating scraping identifiers")
        startpage, nextpage = specs['startpage'], specs['nextpage']
        if 'reconnect' in specs:
            reconnect = specs['reconnect']
        else:
            reconnect = False
        
        progress['link_identifier']     = findlinker(startpage, nextpage).getdict()
        progress['image_identifier']    = findimagefinder(startpage, nextpage).getdict()
        progress['reconnect']           = reconnect
        
        print("Comic Progress:")
        print(progress)
        
        print("- Writing progress file")
        archive.write(progressfile, toml.dumps(progress))
        archive.close()
        print("Done!")
        
    def load(name):
        """Attempts to load the comic with the given name"""
        if not name.endswith(extension):
            name += extension
        path = os.path.join(comicdir, name)
        if not assertpath(path):
            raise Exception("Could not load the comic '{0}'".format(name))
        archive = defaultarchive.load(path)
        metadata = toml.loads(archive.read(metadatafile))
        progress = toml.loads(archive.read(progressfile))
        return Comic(archive, progress, metadata)
    
    def __str__(self):
        return "{0} at page {1}".format(self.metadata['title'], self.progress['lastindex']+1)

def main():
    from utils import getlocal, printiter
    from validators import validate_specs
    print("Testing comic creation...")
    
    specfile = getlocal("testspec.toml")
    with open(specfile) as f:
        specs = toml.load(f)
    directory = os.path.dirname(__file__)
    print("Validating... ", end="")
    valid, errors = validate_specs(specs, directory=directory)
    print("OK" if valid else "FAILED")
    if not valid:
        print("Reason:")
        return printiter(errors)
    
    Comic.create(specs, directory=directory)
    print("Test completed!")
    

if __name__ == '__main__':
    main()