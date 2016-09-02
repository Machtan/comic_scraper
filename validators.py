# coding: utf-8
# Created by Jabok @ August 14th 2014
# validators.py
from validator import validate
import os
"""
Validates comic metadata and specification files
"""

def validate_specs(specdict, directory=None):
    """Validates that a comic can be fetched with the given specs"""
    members = [
        "title",
        "authors",
        "startpage",
        "nextpage"
    ]
    optpaths = [ 
        "descriptionfile",
        "coverfile"
    ]
    return validate(specdict, members, optpaths=optpaths, directory=directory)

def validate_progdata(progdict, directory=None):
    members = [
        "lastimages",
        "reconnect",
        "lastpage",
        "lastindex",
        "link_identifier",
        "image_identifier"
    ]
    return validate(progdict, members, directory=directory)

def validate_metadata(metadict, directory=None):
    """Validates that the given comic metadata is valid"""
    members = [
        "title",
        "authors"
    ]
    optpaths = [
        "descriptionfile",
        "coverfile"
    ]
    return validate(metadict, members, optpaths=optpaths, 
        directory=directory)   