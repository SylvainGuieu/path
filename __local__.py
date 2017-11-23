from __future__ import print_function
from .shared import log, scheme_lookup, connection, remove_roots
import time
from shutil import rmtree
import glob
import os

try:    
    _P3 = False
except:    
    _P3 = True
    basestring = (str, bytes)

class LocalDirectory(object):
    """ Local directory handler """
    def __init__(self, directory, _dummy_=None):
        if _dummy_ is not None:
            raise TypeError("Local directory does not support connection got %s"%dummy)
        self.directory = directory        

    @property
    def dirname(self):
        return self.directory
            
    @property
    def isremote(self):
        return False

    @property
    def connection(self):
        return connection('file', None)
                                   
    def rmtree(self, path):
        """ remove the subrirectory in path """        
        return rmtree(os.path.join(self.directory, path))
                
    def get(self, files='*', inside=None, child=None):
        child = (lambda x:x) if child is None else child #self.fpath

        files = self.ls(files)
        if inside is None or inside==self.directory:    
            return [child( fpath(self.directory, file) ) for file in files]
                                            
        out =[] 
        for file in files:
            orig = os.path.join(self.directory, file)
            dest = os.path.join(inside, file)
            inside.put([file])
            out.append(child(fpath(inside, self.directory)))
        return out                
    
    def put(self, file):
        """ put files in the directory 

        files can be a string glob as e.g. "*.txt" or a list of file path
        """
        if isinstance(files, basestring):
            files = ls(files)            

        for file in files:
            d, filename = os.path.split(file)
            filepath = self.fpath(filename)             
            if filepath != file:
                with open(file,"r") as f:                    
                    filepath.write(f.read())
                    log.notice("file '%s' copied to '%s' "%(file, filepath))                

    def ls(self, glb='*'):
        """ list file in directory from glob. e.g. '*.txt' 

        The returned path are relative 
        """
        if isinstance(glb, basestring):                                
            return remove_roots(glob.glob(os.path.join(self.directory, glb)), self.directory)            
        return [s if os.path.exists(os.path.join(self.directory, s)) else None for s in glb]

    def listdir(self):
    	return os.path.listdir(self.directory)    

    def path_exists(self, path):
        """ true if the relative path exists inside the directory """
        return path in self.ls(path)

    def exists(self):
        """ true if the directory exists """
        return os.path.exists(self.directory)
        #return len(self.ls("."))>0

    def has(self, path):
        """ true if the directory exists """
        return os.path.exists(os.path.join(self.directory, path))
        #return len(self.ls("."))>0    

    def stat(self, file=''):
        return os.stat(os.path.join(self.directory,file))      

    def getmtime(self, file=''):
        return os.path.getmtime(os.path.join(self.directory,file))    

    def getctime(self, file=''):
        return os.path.getctime(os.path.join(self.directory,file))  

    def getatime(self, file=''):
        return os.path.getatime(os.path.join(self.directory,file))                  

    def getsize(self,file=''):
        return os.path.getsize(os.path.join(self.directory,file)) 

    def open(self, file, mode='r'):
        """ open a file inside directory """
        return open(os.path.join(self.directory, file), mode) 
        
    def isfile(self, filename):
        return os.path.isfile(os.path.join(self.directory, filename))
        
    def isdir(self, dirname):
        return os.path.isdir(os.path.join(self.directory, dirname))
        
    def cd(self, a, *p):
        _, connection = self.connection
        path = os.path.normpath(os.path.join(self.dirname, a, *p))
        newdir = self.__class__(path, connection)
        #if not newdir.isdir("."):
        #    raise ValueError("'%s' is not a directory"%path)
        return newdir          
                        
    def makedirs(self, d, noerr=True):    	
        p = os.path.join(self.directory, d)
        try:
            os.makedirs(p)
        except OSError as e:
            if noerr:
                if not os.path.isdir(p):
                    raise e
            else:
                raise e                    
            
    def build(self, noerr=True):
        try:
            os.makedirs(self.directory)
        except OSError as e:
            if noerr:
                if not os.path.isdir(self.directory):
                    raise OSError("[Errno %d] File exists: '%s'"%(os.errno.ENOTDIR, self.directory))
            else:
                raise e
        return self

    def check(self):
        return os.path.exists(self.directory) and os.path.isdir(self.directory)            
            
scheme_lookup['file'] = LocalDirectory