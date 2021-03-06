Introduction
============

Path provide ways to read local or distant directory or file in an
object oriented way. The goal is to provide a way to browse read write
files without having to take care of the root directory (local or
remote).

Example:

    from path import dpath, fpath
    root = dpath("/tmp")
    root.ls()
    f = root.open("today.log") # "today.log" being inside root
    f.read() 

It will works also if root is on a distant ftp server:

    root = dpath("ftp://user:password@someserver.org//tmp")
    root.ls()
    f = root.open("today.log")
    #etc ...

`dpath` stand for directory path and `fpath` for file path, they are
derived from `unicode` objects. So old code using
`root+ '/' + 'today.log'` will still work (if root is local). The `u''`
is replaced by a `d''` for a directory and a `f''` for a file in its
representation.

The string representation of a dpath or fpath is the last argument.

    >>> a = dpath("/tmp", "a")
    >>> a
    d'a'

However the `.path` property gives the relative path to the parent path

    >>> a.path
    d'/tmp/a'
    >>> b = dpath(a, "b") 
    # same as
    >>>> b = a.dpath("b")
    # same as
    >>> b = a.d("b")
    >>> 
    >>> b
    d'b'
    >>> b.path
    d'a/b'

And `.fullpath` the full path build since the first parent

    >>> a = dpath("a")
    >>> b = a.dpath("b")
    >>> c = b.dpath("c")   
    >>> c.fullpath
    d'a/b/c' 

The representation is not necessarily the last component of a path but
can be a path itself:

    >>> root = dpath("/tmp")
    >>> b = root.dpath("a/b")
    >>> b
    d'a/b'

It is important to construct a path with `dpath` or `fpath` in order to
keep the connection (if exists).

`dpath` and `fpath` class can be easily derived. For instance redefining
the `build` method is a good idea to create a structured directory:

     class htmlpath(fpath):
        """ a fpath that point to a html file """
        header = u"""<!DOCTYPE html>
        <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
        <head>
        </head>
        """

     class webpath(dpath):
        """ a dpath that point to a website directory """
        def build(self):
            dpath.build(self)
            # build the subdirectories tree
            self.makedirs("css", "img/large", "img/small", "js")
            # build a index that will have the header defined in htmlpath
            index = htmlpath(self, "index.html").build() 
            # build an empty css/main.css
            fpath(self, "css", "main.css").build()
            return self

        def html_ls(self):
            return self.ls("*.html")     
        def css_ls(self):
            return self.dpath("css").ls("*.css")    

     myweb = webpath("ftp://user:password@server.com/MyPage")
     myweb.build()
     with myweb.open("index.html", "a") as f:
        f.write("<body>Hello this is my web page </body>")

dpath
=====

Take any argument that build the path and on optional keyword which
define the connection if not explicite in the path. So far only 'fttp'
connection and a try of 'http' connection is available.

The rule is to check the url scheme (e.g. `'ftp://'`) and make a
connection. If a user (with or without password) is provided the login
is made on the fly.

    dataDir = dpath("ftp://user:password@server.com/data_directory")

would be equivalent to:

    from ftplib import FTP
    ftp = FTP("server.com")
    ftp.connect()
    ftp.login("user", "password")
    dataDir = dpath( "data_directory", ftp=ftp)  
    dataDir.c is ftp #-> True        

Or better:

    dataDir = dpath("ftp://server.com/", "data_directory")
    dataDir.c.login("user", "password")

dpath also accept the `/` and `//` operand for quick dpath or fpath
creation. `/` create a dpath subdirectory, `//` create a fpath inside
the directory

     >>> d = dpath("/tmp")
     >>> d/"subdir"
     d'/tmp/subdir'
     >>> d//"file.txt"
     f'/tmp/file.txt'

Note that `dpath` and `fpath` are not necessarily related to something
on disk at creation. However, of course, they will be at soon as you use
methods like `.ls`, `.open` etc ....

Properties:
-----------

path\
: a dpath. The relative path to the parent directory

fullpath\
: a dpath. The full path up to the first parent

directory\
: a dpath. dpath of the parent directory or None

c\
: a connection object or None.\
The connection object e.g. FTP object from ftplib

connection\
: connection\_name, connection in a connectiontuple (mapable)

        >>> d = dpath("ftp://user:password@server.com/tmp")
        >>> d.connection
        ('ftp', <ftplib.FTP instance at 0x1038e4830>)
        >>> other = dpath( "other/directory", **d.connection )

ext\
: directory extention

isremote\
: True if the has a remote connection

Methods
-------

unicode methods plus:

open\
: `relativepath, more='r'`\
open the given file inside the diretory

rmtree\
: `relativepath`\
remove the subdirectory defined in path and all its content

get\
: `glb='*', inside=None, child=None`\
get all file defined from glob pattern and put it inside a new directory

ls\
: `glb='*', child=lambda x:x`\
return a list of file find in the directory that match the glob pattern\
child is the wrapper arround returned object.

        d = dpath("ftp://user:password@server.com//tmp")   
        list = d.ls("*.dat", d.fpath)

isroot\
: True if the directory start with the root '/'

makedirs\
: `*subs`\
create a leaf directory and all intermediate ones.

         d = dpath("/tmp/2016-08-12")
         d.build()
         d.makedirs("data/temperatures/", "data/pressure", "logs")
        

This will create the structure :

            /tmp/2016-08-12 
                data/
                    temperatures/
                    pressures/
                logs/         

build\
: build the directory on drive if not exists and return self\
If directory exists stay silence but the directory is a file return a
OSError

        d = dpath("/tmp/2016-08-12").build()

stat\
: attemp to return a stat result of the directory if possible\
not available for ftp connection

getmtime\
: return the modification date if allowed by the connection

getctime\
: return the creation date if allowed by the connection

getatime\
: return the append date if allowed by the connection

dpath\
: `*p`\
return a new dpath object of subdirectories defined in `*p`

        d.dpath("subdirectory")

equivalent of

        dpath(d, "subdirectory")

cd\
: `*p`\
Almost the samething of dpath except that the representation of the
return dpath will contain the parent directory:

        >>> d1 = dpath("/tmp")
        >>> d1.dpath("subdir")
        d'subdir'
        >>> d2.cd("subdir")
        d'/tmp/subdir'

However `d1` and `d2` point to the same phisical directory

fpath\
: `*p`\
return a new fpath where the path defined by `*p` is relative to the
directory

isdir\
: `path`\
return True if the relative path to the directory is a directory.\
not to be confound with `check()` which check is the dpath itself is
what excpected (a directory)

isdir\
: `path`\
return True if the relative path to the directory is a file

exists\
: return True if the dpath exists

psplit\
: split the dpath into two dpath, root and final coponant

        >>> d = dpath("/tmp/a/b/c")       
        >>> d.psplit()
        (d'/tmp/a/b', d'c')

basename\
: return the dpath of the final component

splitext\
: Split the extension return a (dpath, unicode) tuple

          d = dpath("/tmp/config.d")
          d.splitext()
          (d'/tmp/config', u'.d')

expanduser\
: expand the '\~user' to the user path

expandvars\
: expand any \$VAR in the path

        >>> d = path.dpath("$HOME/tmp")
        >>> d.expandvars()
        d'/path/to/my/home/tmp'

has\
: `path`\
return True if the given relative path exists

dbreak\
: `*path`\
return iteraot on subpath

        d = dpath("/tmp") 
        for sub in d.dbreak( "a", "b", "c"):
          sub.build()
          print "directory '%s' created inside '%d"%(sub,d)

Will create the 'tmp/a', '/tmp/b' and '/tmp/c' directories if they do
not exists

fbreak\
: `*path`\
Samething than fbreak but for files

            d = dpath("/tmp")
            for file in d.fbreak("a.txt","b.txt", "c.txt"):
                with file.open("w") as g:
                    g.write("I am the file %s"%file)

checkout\
: check if this is a real directory on disk and return self or raise
TypeError

check\
: return True if the dpath is a directory

dirname\
: same has basename

normpath\
: normatlize the path, ".." and "." are replaced

walk\
: `func, arg`\
Directory tree walk with callback function

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

            >>> exts = (".jpg",".jpeg",".png")
            >>> func = lambda l,d,names: l.extend([f.fullpath for f in names if f.ext.lower() in exts])
            >>> picture_list = []
            >>> d.walk( func , picture_list) 

fpath
=====

As `dpath`, take any argument that build the path and on optional
keyword which define the connection if not explicite in the path. So far
only 'fttp' connection and try of 'http' connection is available.\
Also an extra keyword is 'header' which is used by the build method.

Properties
----------

path\
: a fpath. The relative path to the parent directory

fullpath\
: a fpath. The full path up to the first parent

filename\
: name of file in a string

directory\
: a dpath. dpath of the parent directory or None

ext\
: file extention

body\
: file name body

c\
: a connection object or None.\
The connection object e.g. FTP object from ftplib

connection\
: connection\_name, connection in a connection-tuple (mapable)

        >>> d = dpath("ftp://user:password@server.com/tmp")
        >>> d.connection
        ('ftp', <ftplib.FTP instance at 0x1038e4830>)
        >>> other = dpath( "other/directory", **d.connection )

Methods
-------

unicode methods plus:

open\
: `mode='r'`\
open the file in the given mode

       tempfile = fpath("ftp//user:paswword@server.com/temperature.txt") 
       with tempfile.open('w') as f:
           f.write("temp: 20.5 degree")

stat\
: attemp to return a stat result of the file if possible\
not available for ftp connection

getmtime\
: return the modification date if allowed by the connection

getctime\
: return the creation date if allowed by the connection

getatime\
: return the append date if allowed by the connection

putin\
: `*insides`\
put (copy) the file inside subdirectories

        index = fpath("template/index.html")
        web = dpath("/Library/Server/Web/Documents")
        index.putin( web/"data", web/"log" )

copyto\
: `*tos`\
copy the file to a list of file path

        index = fpath("template/generic_index.html")
        web = dpath("/Library/Server/Web/Documents")
        index.putin( web/"data/index.html", web/"log/index.html" )        

splitext\
: Split the extension return a (fpath, unicode) tuple

          f = fpath("/tmp/config.txt")
          f.splitext()
          (f'/tmp/config', u'.txt')

expanduser\
: expand the '\~user' to the user path

expandvars\
: expand any \$VAR in the path

        >>> f = path.fpath("$HOME/tmp/test.txt")
        >>> f.expandvars()
        f'/path/to/my/home/tmp/test.txt'

normpath\
: normatlize the path, ".." and "." are replaced

basename\
: return the fpath of the final component

dirname\
: return the dpath directory name

build\
: `header=None`\
create the file if it does not exists and return self. A header can be
provided has a string or a function that return a string.\
Also the fpath can have a default header.

        class htmlpath(fpath):
            header = u"""<!DOCTYPE html>
            <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
            <head>
            </head>
            """

        index = htmlpath("index.html").build()
        with index.open('a') as f:
            f.write("<body><h1>This is the main page</h1></body>") 

create\
: `header=None, clobber=False`\
Same as build but raise error if file exists and clobber=False or erase
the file anyway if clobber=True

replace\_ext\
: `newext`\
replace the extention to a new one

        pic = fpath("landscape.JPEG")
        pic = pic.replace_ext("jpg")

exists\
: return True if the fpath exists

psplit\
: split the dpath into (dpath, fpath) tuple

        >>> f = fpath("/tmp/a/b/c.txt")       
        >>> f.psplit()
        (d'/tmp/a/b', f'c.txt')

splitext\
: Split the extension return a (fpath, unicode) tuple

          f = fpath("/tmp/config.d")
          f.splitext()
          (f'/tmp/config', u'.d')
     

check\
: return True is fpath exists and is a file

checkout\
: check if fpath exists and is a file and return self
