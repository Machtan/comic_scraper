# coding: utf-8
# Created by Jabok @ August 14th 2014
# main.py
"""
Entry point for the comic scraping/management program.
Parses command line arguments and invokes the proper functions/submodules.
"""
import sys, os
import toml
from argparse import ArgumentParser
from utils import * # Yes, everything.
from fetcher import fetchcomic

def getlocal(*path):
    return os.path.join(os.path.dirname(__file__), os.path.join(*path))

def parse_scrape(*args):
    """Scrapes a web-based comic"""
    desc="""Scrapes a webcomic from the given specifications.
A specfile or the path of an existing comic must be supplied."""
    prog = os.path.basename(sys.argv[0])+" "+_scrapecmd
    parser = ArgumentParser(description=desc, prog=prog)
    
    parser.add_argument("spec_or_comic", default=None, 
        help="""The title of the comic to scrape, or a file with a 
specification to scrape from.""")
    
    parser.add_argument("-p", "--pages", default=-1, 
        help="""The number of pages to scrape. Defaults to -1, 
meaning 'all'.""")
    
    parser.add_argument("-s", "--startpage", default=None,
        help="The page to start the scrape from")
    
    parser.add_argument("-o", "--overwrite", action="store_true", default=False,
        help="Whether the previous entry for this comic should be overwritten")
    
    args = parser.parse_args(args)
    
    fetchcomic(args.spec_or_comic, overwrite=args.overwrite, 
        startpage=args.startpage, pages=args.pages)            

def printhelp(*args):
    """Prints help text for the commands"""
    program = sys.argv[0]
    if args:
        command = " ".join(args).strip()
        if command in _commands:
            if command in _parsed: # Use argparse help
                _commands[command]("-h")
            else: # Use the docstring
                info = _commands[command].__doc__
                prog = os.path.basename(sys.argv[0])
                prefix = "usage: {0} ".format(prog)
                print(prefix+info)
        else:
            print("Unrecognized command '{0}'".format(command))
    else:
        print("usage: {0} COMMAND [args...]".format(program))
        print("Commands:")
        printiter(sorted(_commands.keys()))
        print("Use 'help COMMAND' for more info.")

_scrapecmd  = "scrape"
_editcmd    = "edit"
_parsed     = {_scrapecmd, _editcmd}
_commands   = {
    _scrapecmd: parse_scrape,
    _editcmd:   edit,
    "list":     listcomics,
    "info":     infocomic,
    "help":     printhelp,
    "patch":    patch,
    "resume":   resume,
    "read":     read
}

def main():
    """Entry point"""
    # Do some simple command parsing
    if not len(sys.argv) > 1:
        command = _commands['help']
    else:
        command = _commands.get(sys.argv[1], _commands['help'])
    command(*sys.argv[2:])
    
if __name__ == '__main__':
    main()