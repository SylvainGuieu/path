#####
# declaration of the dictionary containing 
# the valid connection sheme (file, ftp, etc...) 
######
import os
import glob

scheme_lookup = {}


class connection(tuple):
    """ tuple of a key,value pair that also allow mapping
        so dict(**connection("ftp", FTP("host"))) should work
    """
    def __new__(cl, name, connection):
        self = tuple.__new__(cl, (name, connection))
        return self

    def keys(self):
        return [self[0]]       

    def __getitem__(self, k):
        if isinstance(k , basestring):
            if k!=self[0]:
                raise KeyError("%r"%k)
            return self[1]
        return tuple.__getitem__(self, k)


class _log:
    """ A log class that does nothing unless somebody is declaring 
        an other log class.
        It must have the error, notice and warning functions
    """
    @staticmethod
    def error(*args, **kwargs):
        pass
    @staticmethod            
    def notice(*args,**kwargs):
        pass
    @staticmethod    
    def warning(*args,**kwargs):
        pass
log = _log

def set_log(*args):
    """ Set a log class or log function for the path module 
    
    set_log takes one or 3 arguments:
    - if one argument it must be an object with 3 callable atributes.
        error, warning, notice
    - if three arguments they should be the error, warning and notice 
        callable.
    The error, warning and notice must take only one string argument what 
    they return does not matter.
    
    e.g:
    >>> set_log ( lambda s: print("ERROR: "+s), lambda s: print("WARNING: "+s), lambda s: None)
    will make only the errors and warnings to be displayed

    """
    global log
    if log!=_log:
        raise ValueError("the log functions can only be changed ones")

    if len(args)==1:
        l = args[0]
        for a in ["error", "warning", "notice"]:
            if not hasattr(l, a):
                raise ValueError("log must have a callable '%s' attribute"%a)
        log = l
    elif len(args)==3:
        d = dict((a,staticmethod(f)) for a,f in zip(["error", "warning", "notice"], args))
        log = type("log", tuple(), d)()

    else:        
        raise ValueError("set_log must have exactly one or three arguments")


def remove_roots(lst, root):
    """ remove the root directory in a list of path """
    root = os.path.normpath(root)+"/"
    n = len(root)
    return [l[n:] if l[:n]==root else l for l in (os.path.normpath(l) for l in lst)]


# def real_join(a, *p):
#     """ Same as os.path.join except that the '..' and '.' are handled and removed 

#     real_join( "/a/b/", "..") -> "/a"
#     real_join( "/a/b/", "../..") -> "/"    
#     """
#     leaf = []

#     path = os.path.join(a, *p)
#     return os.path.normpath(path)

#     splited = path.split(os.path.sep)

#     ## if first element is '' that means it was a root
#     if splited and not splited[0]:
#         splited[0] = "/"+splited[0]           
#     for p in splited:
#         if not p or p==".": 
#             continue
#         if p=="..":            
#             try:
#                 l= leaf.pop()
#             except IndexError:
#                 leaf.append(p)
#             else:
#                 if l=="/" and not len(leaf):
#                     leaf =["/.."]
#                     #raise ValueError("relative import below root in '%s'"%path)
                    
#         else:
#             leaf.append(p)
#     return os.path.join(*(leaf or ["."]))

