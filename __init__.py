"""
path provide a way to open, read, copy, move, ... directory or files in a object oriented maner
and without taking care if the file is remote (FTP) or in local drive.
They are two main objects:

dpath : (directory path)
    Accept a string path to a directory 
fpath : (file path)
    Accept a string path to a path

Example
-------
>>> maindir = dpath("/tmp/")
>>> logdir  = maindir.dpath("logs")
>>> with logdir.fpath("today.log") as f:
>>>     print f.read()

One can than change `maindir` to whatever suitable directory. 
It can also be a ftp path:  
>>> maindir = dpath("ftp://user:password@server.com//tmp")
"""
import __file__
del __file__
import __ftp__
del __ftp__
import __http__
del __http__


from .dfpath import fpath, dpath
