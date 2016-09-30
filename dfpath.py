from __future__ import print_function
from .shared import scheme_lookup, remove_roots
from urlparse import urlsplit, urlparse
from .__file__ import LocalDirectory
import os


class dpath(unicode):
    """ Path to a directory 
    
    dpath is derived from a unicode class so that it can be used as a string
    to a directory but has also many functionality. 
    dpath can handle local directory but also distant connection, so far only 
    FTP connection are handled, in a uniform and transparent way. 
    
    Example
    -------

        >>> d = dpath("/path/to/your/directory")
        >>> d.ls()
        [..]
        >>> file = d.fpath("readme.txt")
        >>> print file.open().read()
    
    But the directory can be remote, they are two main ways to open the directory
    remotely:

        >>> from ftplib import FTP
        >>> ftp = FTP("server.com")
        >>> ftp.connect()
        >>> ftp.login("user", "password")
        >>> d = dpath("tmp", ftp=ftp) # 'tmp' directory of you home in the remote machine
    
    Or much faster dpath can recognize the ftp url and if it has
    a login and password it will make the connection for you

        >>> d = dpath("ftp://user:password@server.com/tmp")

    After a connection made one can use it like if it is a local directory

        >>> d.ls()
        [..]

    One can even create a file directly on the server without creating tmp
    file: 

        >>> with d.fpath("data.txt").open("w") as f:
            f.write("2.3 4.5 6.8") 
    
    To get some files:

        >>> lst = d.get("*.dat", "/my/local/directoy")
    
    dpath can take many string arguments and is interpreted as subdirectory path 
    however the string returned will be equal to the last argument:
    
        >>> d = dpath("/a/b/c")
        >>> repr(d)
        d'/a/b/c'
        >>> str(d)
        '/a/b/c'

        >>> d = dpath("/a", "b", "c")
        >>> repr(d)
        "d'c'"
        >>> str(d)
        'c'
        >>> str(d.path)
        '/a/b/c'
    
    One can use a root dpath directory and access to subdirectory without
    having to care if it is local or remote

        >>> root_dir = dpath("ftp://user:password@server.com/data")
        >>> lastdata_dir = dpath(root_dir, "last")
        >>> ### -or- ###
        >>> lastdata_dir = root_dir.dpath("last")
        >>> lastdata_dir
        d'last' in 'ftp://user:password@server.com/data'
    
    
    The dpath class can be derived to make some specific path behavior
     

    """
    def __new__(cl, a, *p, **kwargs):        
        if isinstance(a, tuple(scheme_lookup.values())):
            handler = a
            a = os.path.normpath(handler.directory) # without *p a will be the name
        elif isinstance(a, dpath):
            handler = a.handler                 
        else:
            connection = None
            ## first check if there is anything like ftp=FTP(..)
            for scheme in scheme_lookup:
                if scheme in kwargs:
                    connection = kwargs.pop(scheme)
                    DirClass = scheme_lookup[scheme]
                    break            
            if len(kwargs):
                raise KeyError("only one keyword at a time is accepted")        

            ## then try to look at the string to check any form of 
            ##  e.g: 'ftp://'     
            if connection is None:
                scheme = urlsplit(a).scheme
                if not scheme:
                    # this is a local directory                    
                    DirClass = LocalDirectory
                else:
                    try:
                        DirClass = scheme_lookup[scheme]
                    except KeyError:
                        raise ValueError("'%s' is an unknown scheme for dpath"%scheme)            
            handler = DirClass(a,connection)                 
        
        if len(p)>1:
            ## name is the last argument 
            name = p[-1]
            ## change directory to the subdirectories
            handler = handler.cd(os.path.join(*p))
            if isinstance(a, dpath):
                directory = a.cd(os.path.join(*p[:-1]))
            else:    
                directory = dpath(handler.cd(".."))

        elif len(p)==1:
            ## name is the argument 
            name = p[0]
            handler = handler.cd(*p)
            if isinstance(a, dpath):
                directory = a
            else:    
                directory = dpath(handler.cd(".."))
        else:
            ## name is the only argument 
            name = a
            if isinstance(a, dpath):
                directory = a.directory
            else:
                directory = None    

        new = unicode.__new__(cl, name)
        new.handler = handler
        new._directory = directory
        return new

                
    def __div__(self, right):
        if not isinstance(right, basestring):
            raise TypeError("unsupported operand type(s) for /: 'dpath' and '%s'"%type(right))
        return self.cd(right)
    
    def __floordiv__(self, right):
        if not isinstance(right, basestring):
            raise TypeError("unsupported operand type(s) for /: 'dpath' and '%s'"%type(right))
        return self.fpath(right)
            
    def __repr__(self):
        return "d'%s'"%self
        #if self._rootdirectory:
        #    return "d'%s' in '%s'"%(self , self._rootdirectory)#.handler.directory    
        #else:    
        #    return "d'%s'"%self#.handler.directory    
     
    def open(self, file, mode='r'):
        """ open en a file inside the directory """
        return self.handler.open(file, mode)        
        
    def rmtree(self, path):
        """ remove the subdirectory defined in path and all its content """
        return self.handler.rmtree(path)

    def get(self, glb='*', inside=None, child=None):
        """ get files inside a new directory """
        if inside:
            inside = dpath(inside).build()

        return self.handler.get(glb, inside, child=child)

    def ls(self, glb='*', child=lambda x:x):
        """ return a list of file inside the directory from a glob (e.g '*.txt') expression 
        
        The scond arguemnt child is the wrapper function around file name, it can be a fpath
        or a dpath for instance.
        
            >>> d = dpath("/tmp")
            >>> d.ls("*.txt", d.fpath)
        Or to get path file with the root
            >>> d.ls("*.txt", lambda f:d.fpath(f).path)
        When can also read a bunch of file on the fly:
            >>> d.ls("*.txt", lambda f: (f,d.fpath(f).open.read()))
        """
        if child:
            return [child(el) for el in  self.handler.ls(glb)]        
        return self.handler.ls(glb)    
           
    def isroot(self):
        """ return True if the directory start with the root '/' """
        return os.path.isroot(self)

    def makedirs(self, *subs):
        """ create a leaf directory and all intermediate ones 

        can take several argument that can be independant leaf.
        
        The root directory (self) must be created and exists, that 
        easely achived with the build command : 
            
            >>> d = dpath("/tmp/2016-08-12")
            >>> d.build().makedirs("data/temperatures/", "data/pressure", "logs")
        This will create the structure :
            /tmp/2016-08-12 
                data/
                    temperatures/
                    pressures/
                logs/                             
        """
        if not self.check():            
            raise OSError("the root directory '%s' is not built. Use d.build() to build"%self)
        for d in subs:
            return self.handler.makedirs(d)

    def build(self):
        """ build the directory on drive and return self 
            
            >>> from path import dpath, fpath
            >>> from datetime import date
            >>> root = dpath("/tmp")
            >>> d = root.dpath(str(date.today())).build()
                    
        """
        self.handler.build()        
        return self

    def stat(self):
        """ return a stat result if possible 
    
        For some connection (ftp) the stat result is not available so one has 
        to ask for specific information with getmtime, getctime etc ...
        """
        return self.directory.handler.stat()        

    def getmtime(self):
        """ return the modification date if allowed by the connection """
        return self.handler.getmtime()

    def getctime(self):
        """ return the creation date if allowed by the connection """
        return self.handler.getctime()

    def getatime(self):
        """ return the sccess date if allowed by the connection """
        return self.handler.getatime()              
    
    
                
    def dpath(self, *p):
        """ return a new dpath of subdirectory where the root is self 
        
        d.d is synonyme of d.dpath

        d.dpath("subdirectory") equivalent of dpath(d, "subdirectory")
        """
        return dpath(self, *p)
    d = dpath    
    
    def fpath(self, *p):
        """  return a new fpath file where the root is self 

        d.f is synonyme of d.fpath
        """
        return fpath(self, *p)
    f = fpath    

    def cd(self, *p):
        """ like d.dpath except that the returned dpath object has the root include 

            Note that cd does not do anything on drive.

            >>> d = dpath("/tmp")
            >>> d.dpath("subdir")
            d'subdir'
            >>> d.cd("subdir")
            d'/tmp/subdir'
        
        """
        if self.directory:
            return dpath(self.directory, os.path.join(self, *p))
        else:
            return dpath(os.path.join(self, *p), **self.connection)

    def isdir(self, path):
        """ return True if the given relative path is a directory """
        return self.handler.isdir(path)

    def isfile(self, filename):
        """ return True if the given relative path is a file"""
        return self.handler.isfile(filename)             

    def exists(self):
        """ return True if the path exists """
        return self.handler.exists()
    
    def psplit(self):
        """ split the dpath into two dpath, root and final componant
    
        >>> d = dpath("/tmp/a/b/c")       
        >>> d.psplit()
        (d'/tmp/a/b', d'c')
        
        """
        d1,d2 = os.path.split(self)
        if self.directory is None:
            return dpath(d1, **self.connection), dpath(d1,d2, **self.connection)
        else:            
            return dpath(self.directory, d1), dpath(self.directory,d1,d2)    

    def basename(self):
        """Returns the final component of the pathname in a dpath"""
        _, b = self.split()
        return b

    def splitext(self):
        """Split the extension from a pathname.
        
        Extension is everything from the last dot to the end, ignoring
        leading dots.  Returns "(root, ext)"; ext may be empty and root is a dpath.
        """
        body, ext = os.path.splitext(self)
        if self.directory:
            return dpath(self.directory, body), ext
        else:
            return dpath(body, **self.connection), ext

    def expanduser(self):
        if self.directory:
            return dpath(self.directory, os.path.expanduser(self))
        return dpath(os.path.expanduser(self), **self.connection)

    def expandvars(self):
        if self.directory:
            return dpath(self.directory, os.path.expandvars(self))
        return dpath(os.path.expandvars(self), **self.connection)

    def has(self, path):
        """ return True if the given relative path exists 

            >>> d = dpath("/tmp")
            >>> d.has("results")
            False

        """
        return self.handler.has(path)    


    def path_exists(self, path):
        return self.handler.path_exists(path)

    
    def dbreak(self, *args):
        """ return an iterator where item are sub-dpath of given sub string 

            >>> d = dpath("/tmp")
            >>> for sub in d.dbreak("a","b", "c"):
                print "%r"%sub.path
            d'/tmp/a'
            d'/tmp/b'
            d'/tmp/c'
        """
        for d in args:
            yield self.dpath(d)

    def fbreak(self, *args):        
        """ return an iterator where item are sub-fpath of given sub string 

            >>> d = dpath("/tmp")
            >>> for file in d.fbreak("a.txt","b.txt", "c.txt"):
                with file.open("w") as g:
                    g.write("I am the file %s"%file)
            
            >>> for file in d.fbreak("a.txt","b.txt", "c.txt"):
                with file.open() as f:
                    print "----------------- %s -----------------"%file
                    print f.read()

        Will output:                       
            ----------------- a.txt -----------------
            I am the file a.txt
            ----------------- b.txt -----------------
            I am the file b.txt
            ----------------- c.txt -----------------
            I am the file c.txt                    

        """
        for f in args:
            yield self.fpath(f)        
    
    def checkout(self):
        """ check if this is a real directory on disk and return self or raise TypeError """
        if not self.handler.check():
            raise TypeError("'%s' is not a directory"%self)
        return self   

    def check(self):
        """ return True if self is a directory on disk """
        return self.handler.check()         
        
    def dirname(self):
        d1,d2 = os.path.split(self) 
        if self.directory:
            return dpath(self.directory, d1, d2)
        else:
            return dpath(d1, d2,**self.connection)     

    def walk(self, func, arg):
        """ Directory tree walk with callback function.

        For each directory in the directory tree rooted at top (including top
        itself, but excluding '.' and '..'), call func(arg, d, fnames).
        dirname is the dpath of the directory, and fnames a list of the names of
        the files and subdirectories in dirname (excluding '.' and '..') inside 
        fpath or dpath object. 
        
        func may modify the fnames list in-place (e.g. via del or slice assignment),
        and walk will only recurse into the subdirectories whose names remain in
        fnames; this can be used to implement a filter, or to impose a specific
        order of visiting.  No semantics are defined for, or required of, arg,
        beyond that arg is always passed to func.  It can be used, e.g., to pass
        a filename pattern, or a mutable object designed to accumulate

            >>> d = dpath("tmp")
            >>> dir_list = []
            >>> d.walk( lambda l,d,names: l.append(d.fullpath), dir_list)
            
        Get the path to all jpg or png only             

            >>> func = lambda l,d,names: l.extend([f.fullpath for f in names if f.ext.lower() in (".jpg",".jpeg",".png")])
            >>> picture_list = []
            >>> d.walk( func , picture_list)
                                                                
        """
        top = self
        try:
            names = self.ls("*", lambda s: dpath(s) if self.isdir(s) else self.fpath(s))
        except os.error:
            return
        func(arg, self, names)
        for name in names:
            #name = os.path.join(top, name)
            if self.isdir(name):
                self.dpath(name).walk(func, arg)

    def normpath(self):
        """normatlize the path, ".." and "." are replaced """
        if self.directory:
            return dpath(self.dirname, os.path.normpath(self)) 
        else:
            return dpath(os.path.normpath(self), **self.connection)

    @property
    def connection(self):
        """connection_name, connection  in a connectiontuple (mapable)

        >>> d = dpath("ftp://user:password@server.com/tmp")
        >>> d.connection
        ('ftp', <ftplib.FTP instance at 0x1038e4830>)
        >>> other = dpath( "other/directory", **d.connection )
        """
        return self.handler.connection

    @property
    def ext(self):
        """ file or directory  extention """
        return os.path.splitext(self)[1]    

    @property
    def c(self):
        """a connection object or None"""
        _, c = self.connection
        return c

    @property
    def isremote(self):
        """True if the has a remote connection"""
        return self.handler.isremote

    @property
    def path(self):
        """a dpath or fpath. The relative path to the parent"""
        if self.directory:
            return self.directory.cd(self)
        return dpath(self)

    @property
    def fullpath(self):
        """a dpath or fpath. The full path up to the first parent"""
        top = self
        path = []
        while top:
            path.insert(0, str(top))
            top = top.directory
        return dpath(os.path.join(*path), **self.connection)


    @property
    def directory(self):
        """a dpath or fpath. dpath of the parent directory or None"""
        return self._directory




class fpath(unicode):
    header = None
    def __new__(cl, a, *p, **kwargs): 
        header = kwargs.pop("header", None)

        if len(p)==1:
            directory = dpath(a, **kwargs)
            name = p[0]
            file = name
        elif len(p)>1:
            directory = dpath(a,*p[:-1], **kwargs)
            name = p[-1]
            file = name
        else:
            if isinstance(a, fpath):
                directory = a.directory
                file = a.filename
                header = a.header if header is None else header
            else:    
                directory, file = os.path.split(a)
                directory = dpath(directory, **kwargs) if directory else dpath(".", **kwargs)
            name = a
        
        new = unicode.__new__(cl, name)
        new._filename  = file
        new._directory = directory
        if header is not None:
            new.header = header
            
        return new
        
    def __repr__(self):
        return "f'%s'"%self
        #return "f'%s' in '%s'"%(self, self._rootdirectory)
    
    def open(self, mode='r'): 
        """open the file in the given mode

        Example:

            tempfile = fpath("ftp//user:paswword@server.com/temperature.txt") 
            with tempfile.open('w') as f:
                f.write("temp: 20.5 degree")
        """
        return self.directory.open(self, mode)
     
    def stat(self):
        return self.directory.handler.stat(self.filename)

    def getmtime(self):
        return self.directory.handler.getmtime(self.filename)        

    def getatime(self):
        return self.directory.handler.getatime(self.filename)   
    
    def getctime(self):
        return self.directory.handler.getctime(self.filename)           

    def putin(self, *insides):
        with self.open("rb") as f:
            strin = f.read()            
        for d in insides:
            with dpath(d).open(self.filename, "wb") as g:
                g.write(strin)

    def copyto(self, *tos):
        with self.open("rb") as f:
            strin = f.read()
        for to in tos:  
            with fpath(to).open("wb") as g:
                g.write(strin)

    def replace_ext(self, newext):
        body, ext = os.path.splitext(self.filename)
        return self.__class__(self.directory,  body + newext)
    
    def exists(self):
        return self.directory.path_exists(self.filename)    

    def psplit(self):
        d,f = os.path.split(self)
        if d:
            return dpath(self.directory, d), fpath(self.directory,d,f)
        return self.directory, self

    def splitext(self):
        """Split the extension from a pathname.

        Extension is everything from the last dot to the end, ignoring
        leading dots.  Returns "(root, ext)"; ext may be empty and root is a dpath.
        """
        body, ext = os.path.splitext(self)
        return fpath(self.directory, body), ext

    def expanduser(self):        
        return fpath(self.directory, os.path.expanduser(self))       

    def expandvars(self):        
        return fpath(self.directory, os.path.expandvars(self))
    
    def normpath(self):
        return fpath(self.dirname, os.path.normpath(self))    

    def listdir(self):
        return self.handler.listdir()
         
    def basename(self):
        """Returns the final component of the pathname in a fpath""" 
        d, b = self.psplit()
        return b    

    def dirname(self):
        d1,f = os.path.split(self)         
        return dpath(self.directory, d1)        

    def build(self, header=None):
        """ If the file does not exists create it with all tree structure
        
        Always return self for quick access : 
            f = fpath("/a/b/c").build() 

        A file header can be specified and will be writen in the file if 
        this one does not exists. 
        The fpath object can also have a header attribute taken by default

        Header can also callable method which return a string.
        example : 
            header = fpath("/a/b/header.txt")
            newfile = fpath("/a/b/data.txt")
            newfile.create(header.read)
        """
        if not self.exists():
            self.create(header)
        return self

    def create(self, header=None, clobber=False):
        """ create the file with all the directory tree if necessary 
        
        !! Twhis will erase file contant if clobber=True!!
        
        A file header can be specified and will be writen in the file if 
        this one does not exists. 
        The fpath object can also have a header attribute taken by default        
        
        Header can also callable method which return a string.
        example : 
            header = fpath("/a/b/header.txt")
            newfile = fpath("/a/b/data.txt")
            newfile.create(header.read)
        """
        if not clobber and self.exists():
            raise ValueError("File already exists, user clobber=True to overwrite")

        self.directory.build()
        header = self.header if header is None else header
        if isinstance(header, basestring):
            with self.open("w") as f:
                f.write(header)
        elif hasattr(header, "__call__"):
            with self.open("w") as f:
                f.write(header())            
        elif header is not None:
            raise ValueError("header must be a string or a callable method got a %s object"%type(header))
        else:    
            with self.open("w") as f:
                f.write("")

    def checkout(self):
        """ check if fpath exists and is a file and return self """
        if not self.check():
            raise TypeError("'%s' is not a file"%self)
        return self   

    def check(self):
        """ return True is fpath exists and is a file """
        return self.directory.isfile(self)  

    def dirname(self):
        return self.directory.dirname()

    @property
    def connection(self):
        return self.directory.connection        

    @property
    def c(self):
        return self.directory.c
        
        
    @property
    def filename(self):
        return self._filename
    
    @property
    def directory(self):
        return self._directory
            
    @property
    def ext(self):
        """ file or directory  extention """
        return os.path.splitext(self.filename)[1]

    @property
    def body(self):
        return os.path.splitext(self.filename)[0]    
    
    @property        
    def path(self):
        p = os.path.join(self.directory, self)
        return fpath(p, **dict([self.directory.handler.connection]))

    @property        
    def fullpath(self): 
        p = os.path.join(self.directory.fullpath, self)    
        return fpath("", p, **dict([self.directory.handler.connection]))   
        




