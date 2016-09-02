# coding: utf-8
# Created by Jabok @ August 14th 2014
# main.py
import os, zipfile, tempfile
class ZipArchive:
    """An archive interface for the zip format"""
    def _setmode(self, mode):
        if self.mode != mode:
            #print("Setting mode to '"+mode+"'")
            if self.arch:
                self.arch.close()
            self.mode = mode
            self.arch = zipfile.ZipFile(self.path, mode=self.mode, compression=self.comp)
        
    def __init__(self, filepath, mode, comp=zipfile.ZIP_DEFLATED):
        self.path = filepath
        self.comp = comp
        self.mode = None
        self.arch = None
        self._setmode(mode)
        
    def create(filepath):
        return ZipArchive(filepath, "a")
    
    def load(filepath, mode='r'):
        if not mode in ["a", "r"]:
            raise Exception("Archive must be opened in modes 'r' or 'a'!")
        if not os.path.exists(filepath):
            raise Exception("Archive file not found: '{0}'".format(filepath))
        else:
            return ZipArchive(filepath, mode=mode)
    
    def read(self, member):
        self._setmode("r")
        return str(self.arch.read(member), encoding="utf-8")
    
    def write(self, member, content):
        self._setmode("a")
        return self.arch.writestr(member, content)
    
    def close(self):
        return self.arch.close()
            
    def list(self):
        return list([info.filename for info in self.arch.infolist()])