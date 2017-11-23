from __future__ import print_function
from .shared import log, scheme_lookup, connection
from .__local__ import LocalDirectory
from ftplib import FTP, error_perm, error_temp, all_errors
try:
    from urlparse import urlsplit, urlparse #python 2.7
except:
    from urllib.parse import urlsplit, urlparse

import time
import glob
import os
try:
    from StringIO import StringIO # python 2.7
    _P3 = False
except:
    from io import StringIO, BytesIO # python 3
    _P3 = True


VERBOSE = True
FORCE = True


class FtpDirectory(LocalDirectory):
    """ Directory handler with FTP connection """
    ftp = None

    def __init__(self,  url, ftp=None):
        """ a path to a ftp directory """
        url = urlsplit(url)        
        if url.scheme:
            if url.scheme not in ["ftp","sftp"]:
                raise ValueError("scheme must be 'ftp://' for a FtpDirectory")
            if ftp is None:
                ftp = FTP(url.hostname, url.username, url.password)
                #ftp = FTP(url.hostname)
                ftp.connect(url.hostname, url.port or 0)
                if url.username:
                    ftp.login(url.username, url.password)

                ## store the username in the ftp so it can recovered later
                ftp.username = url.username
                username = url.username
                hostname = url.hostname              
            else:
                username = getattr(ftp, "username", url.username or "")
                hostname = getattr(ftp, "hostname", url.hostname or "")
                #ftp.connect(url.hostname)
                #ftp.login(url.username, url.password)    

            directory = url.path[1:] # remove the first '/' so the path 
                                     # is relative to the connection point 
            
            ## do not use the url.geturl() method in order to 
            ## remove the password from the url representation 
            path = '%s://'%url.scheme
            if username:
                path += username + "@"
            path += hostname + "/" + directory
                    
        else:
            if ftp is None:
                raise ValueError("if no explicite sceme is present in url, a valid ftp connection must be present")
            username = getattr(ftp, "username", url.username)
            directory = url.path
            path = "ftp://%s%s/%s"%(username+"@" if username else "", ftp.host, directory)
        
        LocalDirectory.__init__(self, path) 

        self.remotedirectory = directory        
        self.ftp = ftp        

    @property
    def dirname(self):
        return self.remotedirectory
        
    @property
    def isremote(self):
        """ True if the directory is in remote access """
        return True            

    @property
    def connection(self):
        return connection('ftp', self._get_ftp())

    def _get_ftp(self):
        return self.ftp

    def login(self, user, password):
        return self._get_ftp().login(user, password)

    def put(self, files):
        """ put files in the directory 

        files can be a string glob as e.g. "*.txt" or a list of file path
        """
        ftp = self._get_ftp()

        if isinstance(files, basestring):
            files = ls(files)            

        for file in files:
            with open(file,'rb') as f:
                d, filename = os.path.split(file)              
                ftp.storbinary('STOR %s'%os.path.join(self.remotedirectory,filename), f)     # send the file
                log.notice("file '%s' transfered in '%s' "%(file, self.directory))
    

    def rmtree(self, path):
        """ remove the subrirectory in path """
        ftp = self._get_ftp()        
        return ftp_rmtree(ftp, os.path.join(self.remotedirectory, path))

    def ls(self, glob='*'):
        """ list file in directory from glob. e.g. '*.txt' 

        The returned path are relative 
        """
        ftp = self._get_ftp() 
        glob = ftp_path2path(ftp, glob)         
        return remove_roots(ftp_ls(ftp, os.path.join(self.remotedirectory,glob)), self.remotedirectory)        

    def listdir(self):
        ftp = self._get_ftp()
        return ftp.nlst()
        
    def get(self, files, inside, child=None):
        """ 
        Parameters
        ----------
        files : string
            file glob 
        """
        child = child or self.fpath

        ftp = self._get_ftp()
        file = ftp_path2path(ftp, file)        
        return [child(f) for f in ftp_mget(ftp, os.path.join(self.remotedirectory, files), inside)]

    if _P3:
        def open(self, file, mode='r'):    
            """ open a file inside directory """ 
            ftp =  self._get_ftp()
            file = ftp_path2path(ftp, file)
            #print ("FTP %s"% os.path.join(self.remotedirectory, file))
            if 'b' in mode:
                return FtpBytesFile(ftp, os.path.join(self.remotedirectory, file), mode)  
            else:
                return FtpFile(ftp, os.path.join(self.remotedirectory, file), mode)  

    else:
        def open(self, file, mode='r'):    
            """ open a file inside directory """ 
            ftp =  self._get_ftp()
            file = ftp_path2path(ftp, file)
            #print ("FTP %s"% os.path.join(self.remotedirectory, file))
            return FtpFile(ftp, os.path.join(self.remotedirectory, file), mode)  

    def getmtime(self,file=''):
        ftp = self._get_ftp()
        file = ftp_path2path(ftp, file)

        t = ftp.sendcmd("MDTM %s"%(os.path.join(self.remotedirectory, file)))
        t = time.strptime(t[4:], "%Y%m%d%H%M%S")
        return time.mktime(t)

    def stat(self, file=''):
        raise RuntimeError("Cannot get stat from ftp connection. Modification date only")  

    def getatime(self, file=''):
        raise RuntimeError("Cannot get access time from ftp connection. Modification date only")    

    def getctime(self, file=''):
        raise RuntimeError("Cannot get creation time from ftp connection. Modification date only")            
    
    def getsize(self, file=''):
        ftp = self._get_ftp()
        file = ftp_path2path(ftp, file)        
        return ftp.size(os.path.join(self.remotedirectory, file))
        #raise RuntimeError("Cannot get size from ftp connection. Modification date only")            
        


    def exists(self):
        return self.remotedirectory in self.cd("..").ls()

    def has(self, path):
        return path in self.ls()       
        
    def append(self, file, strin):
        f = self.open(file)
        f.seek(0,2)
        f.write(strin)
        f.seek(0)
        ftp = self._get_ftp()
        ftp.storbinary('STOR %s'%os.path.join(self.remotedirectory,file), f)

    def appendlines(self, file, lines):
        f = self.open(file)
        f.seek(0,2)
        f.writelines(lines)
        f.seek(0)
        ftp = self._get_ftp()
        ftp.storlines('STOR %s'%os.path.join(self.remotedirectory,file), f)

    def isfile(self, filename):
        ftp = self._get_ftp()
        filename = ftp_path2path(ftp, filename)     
        return ftp_isfile(ftp, os.path.join(self.remotedirectory, filename))    

    def isdir(self, dirname):
        ftp = self._get_ftp()
        dirname = ftp_path2path(ftp, dirname)
        return not ftp_isfile(ftp, os.path.join(self.remotedirectory, dirname))                   

    def _path(self, relpath, ftp):
        ftppath  = os.path.join(self.remotedirectory, relpath)
        path = (self,)+relpath

        if ftp_isfile(ftp, os.path.join(ftppath)):            
            return fpath(*path)

        return dpath(*path)

    def makedirs(self, d):
        ftp = self._get_ftp()
        d = ftp_path2path(ftp,d)        
        ftp_makedirs(ftp, os.path.join(self.remotedirectory,d), True)

    def build(self):
        ftp = self._get_ftp()
        ftp_makedirs(ftp, self.remotedirectory, True)
        return 

        try:
            ftp_makedirs(ftp, self.remotedirectory, True)
        except error_perm as e:
            if "550" in str(e)[:4]:
                if ftp_isfile(ftp, self.remotedirectory):
                    raise OSError("[Errno %d] File exists: '%s'"%(os.errno.ENOTDIR, self.directory))                                    
            else:
                raise error_perm(e)
        return self    
    
    def check(self):
        ftp = self._get_ftp()
        return ftp_exists(ftp, self.remotedirectory) and  not ftp_isfile(ftp, self.remotedirectory)


######################################################
#
# Record this ftp handler class to the shared sheme_lookup
#
######################################################
scheme_lookup['ftp'] = FtpDirectory


class FtpFile(StringIO): 
    def __init__(self, ftp,  file, mode='r'):
        self.ftp = ftp 
        self.file = file
        if 'r' in mode or 'a' in mode:
            buf = self._ftpread()
        if 'w' in mode:
            buf = ''
        StringIO.__init__(self, buf)            
        if 'a' in mode:
            self.seek(0,2)        
        self.mode = mode

    def __repr__(self):
        return "<open file '%s' in ftp '%s', mode '%s' at %0x>"%(self.file, self.ftp.host, self.mode, id(self))

    if _P3:
        def _ftpread(self):
            ftp = self.ftp
            strout = BytesIO()
            ftp.retrbinary("RETR %s"%(self.file), strout.write)
            strout.seek(0)
            return strout.read().decode()
    else:
        def _ftpread(self):
            ftp = self.ftp
            strout = StringIO()
            ftp.retrbinary("RETR %s"%(self.file), strout.write)
            strout.seek(0)
            return strout.read()

    if _P3:
        def _ftpwrite(self, strin):
            f = BytesIO(strin.encode())
            ftp = self.ftp            
            ftp.storbinary('STOR %s'%(self.file), f) 

    else:
        def _ftpwrite(self, strin):
            f = StringIO(strin)
            ftp = self.ftp
            ftp.storbinary('STOR %s'%(self.file), f)            

    def close(self):
        mode = self.mode
        if not 'r' in mode:
            self.seek(0)            
            self._ftpwrite(self.read())        
        StringIO.close(self)

    @property
    def name(self):
        return self.file
    @property
    def path(self):
        return fpath(file, ftp=self.ftp)

    def __del__(self):
        if not self.closed:                
            self.close()

    def __exit__(self, *args):
        self.close()

    def __enter__(self):
        return self        



if _P3:
    class FtpBytesFile(BytesIO): 
        def __init__(self, ftp,  file, mode='rb'):
            self.ftp = ftp 
            self.file = file
            if not 'b' in mode:
                raise RunTimeError("should be opened as binary")

            if 'r' in mode or 'a' in mode:
                buf = self._ftpread()
            elif 'w' in mode:
                buf = b''
            else:
                buf = self._ftpread()
            BytesIO.__init__(self, buf)            
            if 'a' in mode:
                self.seek(0,2)        
            self.mode = mode

        def __repr__(self):
            return "<open file '%s' in ftp '%s', mode '%s' at %0x>"%(self.file, self.ftp.host, self.mode, id(self))

        
        def _ftpread(self):
            ftp = self.ftp
            strout = BytesIO()
            ftp.retrbinary("RETR %s"%(self.file), strout.write)
            strout.seek(0)
            return strout.read()
    
        def _ftpwrite(self, bytesin):
            f = BytesIO(bytesin)
            ftp = self.ftp            
            ftp.storbinary('STOR %s'%(self.file), f) 

        def close(self):
            mode = self.mode
            if not 'r' in mode:
                self.seek(0)            
                self._ftpwrite(self.read())        
            BytesIO.close(self)

        @property
        def name(self):
            return self.file
        @property
        def path(self):
            return fpath(file, ftp=self.ftp)

        def __del__(self):
            if not self.closed:                
                self.close()

        def __exit__(self, *args):
            self.close()

        def __enter__(self):
            return self        


#####################################################################
#
#  FTP high level functions 
#
#####################################################################

def ftp_path2path(ftp,path):
    """ take a ftp connection and a path return the true path 
    if path is an url or path. 
    If the url hostanme or login is different than 
    """
    url = urlsplit(path)
    if not url.hostname:
        return path
    if url.hostname!=ftp.host:
        raise ValueError("connection mismatch : '%s', '%s'"%(url.hostname, ftp.host))

    if url.username and url.username!=getattr(ftp,"username", url.username):
        raise ValueError("connection username mismatch : '%s', '%s'"%(url.username, ftp.username))
    return url.path[1:] # remove the root '/'




def remove_roots(lst, root):
    root = os.path.normpath(root)+"/"
    n = len(root)
    return [l[n:] if l[:n]==root else l for l in (os.path.normpath(l) for l in lst)]



def _ftp_exists(ftp, path):
    r, d = os.path.split(path)
    return os.path.join(r,d) in ftp.nlst(r)

def _ftp_dir(ftp, pathes, pref, output):
    
    if not len(pathes):
        try:
            lst = [pref] if pref and (len(ftp.nlst(pref)) or _ftp_exists(ftp, pref))  else []
            ## if belowe line uncomment it will end up with a one depth more 
            #lst = ftp.nlst(pref) if pref else ftp.nlst() 
        except error_temp as e:
            code = str(e).split(" ")[0]
            if code!='450':
                raise e
        else:       
        #output.append(pref)
        
            output.extend(lst)
        return 0

    glb = pathes[0]
    pathes.pop(0)

    if not glob.has_magic(glb):
        
        return _ftp_dir(ftp, pathes, os.path.join(pref,glb), output)  

    try:
        lst = ftp.nlst(pref) if pref else ftp.nlst()
    except error_temp as e:
        code = str(e).split(" ")[0]
        if code!='450':
            raise e
        
        return len(pathes)
    else:
        if len(lst)==1 and lst[0]==pref: # this is a file not a directory
            
            return len(pathes) 
        for item in lst:            
            _, f = os.path.split(item)
            if glob.fnmatch.fnmatch(f, glb):
                _ftp_dir(ftp, list(pathes), item, output)
    return len(pathes)

def ftp_ls(ftp, glb):
    output = []
    pathes = glb.split("/")
    pref = ""
    if pathes and glb[0]=="/":
        pathes[0] = "/"+pathes[0]
    _ftp_dir(ftp, pathes, pref, output)
    return output


def ftp_isfile(ftp, path):
    try:
        lst = ftp.nlst(path)
    except error_perm:
        return False
    return len(lst)==1 and lst[0]==path

def ftp_exists(ftp, path):
    _, d = os.path.split(path)    
    return d in [os.path.split(s)[1] for s in ftp.nlst(os.path.join(path, ".."))]


def _ftp_makedirs(ftp, pathes, pref, noerr):
    if not len(pathes):
        return 0
    d = pathes[0]
    pathes.pop(0)
    d = os.path.join(pref,d)
    try:
        ftp.mkd(d)
    except error_perm as e:        
        #if not len(pathes):
            if noerr:                
                if ftp_isfile(ftp, d):
                    raise error_perm("550 %s: File exists."%d)
            else:
                raise error_perm(e)        
    return _ftp_makedirs(ftp, pathes, d, noerr)       

def ftp_makedirs(ftp, dirs, noerr=False):
    pathes = dirs.split("/")
    if pathes and dirs[0]=="/":
        pathes[0] = "/"+pathes[0]
    _ftp_makedirs(ftp, pathes, "", noerr)

def ftp_dirlist(ftp, directory, verbose=VERBOSE):
    """
    Return a list of file of the directory in ftp connection
    the returned list does not contain the directory path
    """
    listfile = []
    log.notice("Changing distant directory to %s"%(directory))

    rtr = ftp.cwd(directory)
    log.notice("%s"%(rtr))
    log.notice("Get file list ")

    rtr = ftp.retrlines('NLST', listfile.append)
    log.notice("%s"%(rtr), verbose)

    return listfile



def ftp_rmtree(ftp, path):
    """Recursively delete a directory tree on a remote server."""
    wd = ftp.pwd()

    try:
        names = ftp.nlst(path)
    except all_errors as e:
        # some FTP servers complain when you try and list non-existent paths
        return

    for name in names:
        if os.path.split(name)[1] in ('.', '..'): continue


        try:
            ftp.cwd(name)  # if we can cwd to it, it's a folder
            ftp.cwd(wd)  # don't try a nuke a folder we're in
            ftp_rmtree(ftp, name)
        except all_errors:
            ftp.delete(name)

    try:
        ftp.rmd(path)
    except all_errors as e:        
        return

def local_rmtree(path):
    import shutil
    shutil.rmtree(path)


def _ftp_glob_dirlist_rec(ftp, path_list, pref="", verbose=VERBOSE):
    # walk through the path_list to get a list of files
    # ftp NLST to not allows to list a path of directory with the * like /tmp/*/*.txt
    # so we need to split the path and goes directory by directory if needed

    if not len(path_list):
        return []

    directory_glob  = path_list.pop(0)
    if not glob.has_magic( directory_glob ):
        if not len(path_list):
            # end of the recursive call, just return the list
            file_list = []
            ftp.retrlines("NLST %s"%pref+directory_glob , file_list.append)
            return file_list
        else:
            # if no magic found just stick to the prefix and send the rest of
            # path_list as a copy: list(path_list)
            return _ftp_glob_dirlist_rec(ftp, list(path_list), pref=pref+directory_glob+"/", verbose=verbose)

    directory_found = []

    # the following line works only with * not with more complex glob [0-9] etc ...
    #rtr     = ftp.retrlines("NLST %s"%pref+directory_glob , directory_found.append)
    # So we need to list all the directory and then match the files
    ftp.retrlines("NLST %s"%pref, directory_found.append)
    #pref_len = len(pref)
    #directory_found = [l for l in directory_found if glob.fnmatch.fnmatch(l[pref_len:], directory_glob)]
    directory_found = [l for l in directory_found if glob.fnmatch.fnmatch(os.path.split(l)[1], directory_glob)]

    if not len(path_list):
        return directory_found

    output = []

    for d in directory_found:
        # list(path_list) to make a copy
        fls =  _ftp_glob_dirlist_rec(ftp, list(path_list), pref=d+"/", verbose=verbose)
        # extend the output with the new found
        output.extend(fls)
    return output




###############################################
# old stuf 

def ftp_put(ftp, local, remote):        
    with open(local, 'rb') as f:        
        ftp.storbinary('STOR %s'%remote, f)     # send the file
    return remote

def ftp_get(ftp, remote, local):
    with open(local, "wb") as f:
        ftp.retrbinary("RETR %s"%(remote),f.write)
    return local    

def ftp_mget(ftp, remotes, localdir):
    if isinstance(remotes, basestring):
        files = ftp_ls(ftp, remotes)
    else:
        files = list(remotes)

    lst = []    
    for remote in files:
        _, name = os.path.split(remote)
        lst.append(ftp_get(ftp, remote, os.path.join(localdir, name)))
    return lst    

def ftp_mput(ftp, flocals, remotedir):
    if isinstance(flocals, basestring):
        files = glob.glob(flocals)
    else:
        files = list(flocals)

    lst = []    
    for local in files:
        _, name = os.path.split(remote)
        lst.append(ftp_put(ftp, local, os.path.join(remotedir, name)))
    return lst   


def ftp_lsdir(ftp, strglob, verbose=VERBOSE):
    """
    ftp_lsdir(ftp, str)
    do the same thing than lsdir but for a ftp connection.
    """
    return ftp_glob_dirlist_rec(ftp, strglob, verbose=verbose)

def ftp_glob_dirlist_rec( ftp, path, verbose=VERBOSE):
    path_list =  path.split("/")
    pref = ""
    if len(path_list) and path_list[0] == "":
        path_list.pop(0)
        pref= "/"
    log.notice( "Looking for '%s:%s' in ftp connection ... "%(ftp.host,path) )
    files=  _ftp_glob_dirlist_rec(ftp, path_list, pref, verbose=verbose)
    log.notice( "found %d"%(len(files)) )
    return files





def ftp_transfer(ftp, strglob, localdir= "",distdir="",
                 verbose=VERBOSE, force=FORCE):
    """
    ftp_transfer(ftp, strglob, localdir= "",distdir="")
    Transfer file matching strglob from the ftp connection. The hierarchic path directory
    will be created from the localdir.
    distdir is the distant root ftp directory starting point, is equivalent
    to do a ftp.cwd( distdir) to change directory.

    """
    if distdir and len(distdir):
        ftp.cwd(distdir)
    files = ftp_lsdir(ftp, strglob, verbose=verbose)
    if not len(files):
        return []
    return ftp_transfer_files( ftp, files, localdir=localdir,
                               distdir=distdir,
                               verbose=verbose, force=force)



def ftp_transfer_files(ftp,  files, localdir= "", distdir="", verbose=VERBOSE, force=FORCE):
    """
    Transfer a list of files from the ftp connection. The hierarchic path directory
    will be created from the localdir.
    distdir is the distant root ftp directory starting point, is equivalent
    to do a ftp.cwd( distdir) to change directory.

    Return the list of local path to files
    """
    if os.path.exists(localdir):
        if not os.path.isdir(localdir):
            raise Exception("The local path '%s' is not a directory"%(localdir))
    else:
        os.makedirs(localdir)       
    if distdir and distdir!="":
        ftp.cwd(distdir)

    global _ftpfinished
    global _ftpwrfunc


    outlist = []
    for path in files:
        subdir, fl = os.path.split(path)
        if subdir[0:len(distdir)] == distdir:
            subdir = subdir[len(distdir):]
        create_dir(subdir, localdir, verbose=verbose)
        localpath = os.path.join(localdir, subdir, fl)

        if not force and os.path.exists(localpath):
            log.notice("file %s already exists use force=True to force download"%(localpath))
        else:
            log.notice("FTP: Copying file %s:%s to %s "%(ftp.host, fl, localdir+subdir))

            try:
                ftp.retrbinary("RETR %s"%(path),open(localpath, "wb").write)
            except error_perm:
                log.warning("wrong permition for transfert %s"%path)    
        outlist.append( localpath )
    return outlist


def ftp_put_file(ftp, file, distdir=""):
    if distdir:
        ftp.cwd(distdir)
    d, filename = os.path.split(file)        
    file = open(file,'rb')                  # file to send
        
    ftp.storbinary('STOR %s'%filename, file)     # send the file
    log.notice("file '%s' transfered in '%s/%s' "%(filename,ftp.host, ftp.user()))
    file.close()

def create_dir(directory,inside="", verbose=VERBOSE):
    """
    recreate is necessary a directory structure from a path string  "a/b/c" or a list ["a","b","c"]
    The second argument precise where the structure should be installed
    so create_dir( "data/set1", "/tmp")  is the same than create_dir( "tmp/data/set1")

    """

    if not os.path.isdir(inside):
        raise Exception( "'%s' is not a directory"%inside)
    if isinstance( directory, basestring):
        # save time exist if exists
        if os.path.isdir(os.path.join( inside,directory)):
            return None
        directories = directory.split("/")
    else:
        directories = directory
        if os.path.isdir(os.path.join(inside, *directories)):
            return None

    sub = inside
    while len(directories):
        sub += "/"+directories.pop(0)

        if os.path.exists(sub):
            if not os.path.isdir(sub):
                raise Exception("'%s' exists but is not a directory "%(sub))
        else:
            log.notice( verbose, "Creating directory %s"%sub)
            os.mkdir(sub)
    return None
