import os
from .dfpath import fpath,dpath

def exists(path):
    """Test whether a path exists.  Returns False for broken symbolic links"""
    if isinstance(path, (fpath, dpath)):
        return path.exists()
    return os.path.exists(path)
        
def splitext(path):
    """Split the extension from a pathname.

    Extension is everything from the last dot to the end, ignoring
    leading dots.  Returns "(root, ext)"; ext may be empty.
    """
    if isinstance(path, (fpath, dpath)):
        return path.splitext()
    return os.path.splitext(path)

def basename(p):
    """Returns the final component of a pathname""" 
    if isinstance(path, fpath):
        fpath(path.directory, *os.path.split())

def walk(top, func, arg):
    """Directory tree walk with callback function.

    For each directory in the directory tree rooted at top (including top
    itself, but excluding '.' and '..'), call func(arg, dirname, fnames).
    dirname is the name of the directory, and fnames a list of the names of
    the files and subdirectories in dirname (excluding '.' and '..').  func
    may modify the fnames list in-place (e.g. via del or slice assignment),
    and walk will only recurse into the subdirectories whose names remain in
    fnames; this can be used to implement a filter, or to impose a specific
    order of visiting.  No semantics are defined for, or required of, arg,
    beyond that arg is always passed to func.  It can be used, e.g., to pass
    a filename pattern, or a mutable object designed to accumulate
    statistics.  Passing None for arg is common.
    """
    if isinstance(top,  dpath):
        return dpath.walk(func, arg)
    os.path.walk(top, func, arg)        


def expanduser(p):
    """Expand ~ and ~user constructions.  If user or $HOME is unknown,
    do nothing.
    """
    if isinstance(p, (fpath,dpath)):
        return p.expanduser()

    return os.path.expanduser(p)    

def getmtime(p):
    """Return the last modification time of a file, reported by os.stat()."""
    if isinstance(p, (fpath,dpath)):
        return p.getmtime()
    return os.path.getmtime(p)
        
def getatime():
    """Return the last access time of a file, reported by os.stat()."""
    if isinstance(p, (fpath,dpath)):
        return p.getatime()
    return os.path.getatime(p)

def getctime():
    """Return the metadata change time of a file, reported by os.stat()."""
    if isinstance(p, (fpath,dpath)):
        return p.getctime()
    return os.path.getctime(p)

def dirname(p):
    """Returns the directory component of a pathname"""
    if isinstance(p,(fpath,dpath)):
        return p.dirname()
    return os.path.dirname(p)       

def isfile(p):
    """Test whether a path is a regular file"""
    if isinstance(p, fpath):
        return p.check()
    if isinstance(p, dpath):
        return False
    return os.path.isfile(p)            

def isdir(p):
    """Return true if the pathname refers to an existing directory."""
    if isinstance(p, dpath):
        return p.check()
    if isinstance(p, fpath):
        return False
    return os.path.isfile(p)

def getsize(p):
    """Return the size of a file, reported by os.stat()."""
    if isinstance(p, (fpath,dpath)):
        return p.getsize()
    return os.path.getsize(p)


def abspath(p):
    """Return an absolute path."""
    if isinstance(p, (fpath,dpath)):
        return p.path
    return os.path.abspath(p)   

def islink(p):
    """Test whether a path is a symbolic link"""
    return os.path.islink(p)    


def split(p):
    """Split a pathname.  Returns tuple "(head, tail)" where "tail" is
    everything after the final slash.  Either part may be empty.
    """
    if isinstance(p, (fpath,dpath)):
        return p.psplit()
    return os.path.split(p) 

def samefile(p1,p2):
    """Test whether two pathnames reference the same actual file"""
    if isinstance(p, (fpath,dpath)):
        return p1.directory == p2.directory and\
               p1 == p2
    return os.path.samefile        

def expandvars(p):
    """Expand shell variables of form $var and ${var}.  Unknown variables
    are left unchanged."""
    if isinstance(p, (fpath,dpath)):
        return p.expandvars()
    return os.path.expandvars(p)    

def join(a, *p):
    """Join two or more pathname components, inserting '/' as needed.
    If any component is an absolute path, all previous path components
    will be discarded.  An empty last part will result in a path that
    ends with a separator.
    """
    if isinstance(a, dpath):
        return a.cd(*p)
    return os.path.join(a,*p)   

def normpath(p):
    """Normalize path, eliminating double slashes, etc."""
    if isinstance(p, (fpath,dpath)):
        return p.normpath()
    return os.path.normpath(p)

isabs = os.path.isabs
commonprefix = os.path.commonprefix
lexists = os.path.lexists
samestat = os.path.samestat

ismount = os.path.ismount
sameopenfile = os.path.sameopenfile
splitdrive = os.path.splitdrive
relpath = os.path.relpath
realpath = os.path.realpath