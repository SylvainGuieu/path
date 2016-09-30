## experimental 
# uQvwg63reC%u
from __future__ import print_function
from .shared import log, scheme_lookup, connection
from .__file__ import LocalDirectory
from ftplib import FTP, error_perm, error_temp, all_errors
from urlparse import urlsplit, urlparse

import time
import glob
import os
import StringIO

from bs4 import BeautifulSoup
import requests


class HttpHandler(LocalDirectory):
    def __init__(self, url, http=None):
        if http  and not isinstance(http, requests.Response):
            raise ValueError("expecting a requests response got "%type(http))

        url = urlsplit(url)        
        if url.scheme:
            if url.scheme not in ["http"]:
                raise ValueError("scheme must be 'http://' for a FtpDirectory")
            if http is None:
                http = requests.get(url.geturl())
                #ftp = FTP(url.hostname)
                
                ## store the username in the ftp so it can recovered later
                http.username = url.username
                username = url.username
                hostname = url.hostname              
            else:
                username = getattr(http, "username", url.username or "")
                hostname = getattr(http, "hostname", url.hostname or "")
                #ftp.connect(url.hostname)
                #ftp.login(url.username, url.password)    
            
            directory = url.path # remove the first '/' so the path 
                                     # is relative to the connection point 
            
            path = url.geturl()
        else:
            if http is None:
                raise ValueError("if no explicite sceme is present in url, a valid htp request  must be present")
            directory = url.path                
            path = os.path.join(http.url, directory)

        if not hasattr(http, "hrefs"):
            http.hrefs = {}
        if not hasattr(http, "srcs"):
            http.srcs = {}    

        LocalDirectory.__init__(self, path)
        self.remotedirectory = directory
        self.http = http
    
    @property
    def dirname(self):
        return self.remotedirectory
        
    @property
    def isremote(self):
        """ True if the directory is in remote access """
        return True            

    @property
    def connection(self):
        return connection('http', self.http)    
    
    def put(self, files):
        raise TypeError('http connection is readonly')
    
    def rmtree(self, path):
        raise TypeError('http connection is readonly')
    
    def makedirs(self, path):
        raise TypeError('http connection is readonly')
    
    def get_hrefs(self):
        directory  = self.remotedirectory
        try:
            hrefs = self.http.hrefs[directory]
        except KeyError:
            hrefs = list(http_hrefs(requests.get((self.http.url+'/'+self.remotedirectory))))
            self.http.hrefs[directory] = hrefs
        return hrefs

    def get_srcs(self):
        directory  = self.remotedirectory
        try:
            srcs = self.http.srcs[directory]
        except KeyError:
            srcs = list(http_srcs(requests.get((self.http.url+'/'+self.remotedirectory))))
            self.http.srcs[directory] = srcs
        return srcs    

    def ls(self, glb="*"):
        glb = http_path2path(self.http, glb)
        lst = self.get_hrefs()+self.get_srcs()        
        lst = [f for f in lst if glob.fnmatch.fnmatch(f, glb)]
        return lst        

    def isfile(self, filename):
        return True

    def isdir(self, dirname):
        return False
    
    def check(self):
        return True 

    def open(self, file, mode='r'):    
        """ open a file inside directory """         
        file = http_path2path(self.http, file)
        #print ("FTP %s"% os.path.join(self.remotedirectory, file))
        return HttpFile(self.http, os.path.join(self.remotedirectory, file), mode)  

scheme_lookup['http'] = HttpHandler


class HttpFile(StringIO.StringIO): 
    def __init__(self, http,  file, mode='r'):
        if 'w' in mode or 'a' in mode:
            raise OSError("http file are read only")
        
        buf = requests.get(os.path.join(http.url, file)).text
                
        StringIO.StringIO.__init__(self, buf)                          
        self.file = file
        self.host = urlsplit(http.url).hostname    
        self.http = http
    def __repr__(self):
        return "<open file '%s' in http '%s', mode 'r' at %0x>"%(self.file, self.host, id(self))
       

    @property
    def name(self):
        return self.file

    @property
    def path(self):
        return fpath(file, http=self.http)

    # def __del__(self):
    #     self.close()
                        
    # def __exit__(self, *args):
    #     self.close()

    # def __enter__(self):
    #     return self        






def http_hrefs(http):
    soup = BeautifulSoup(http.text, 'html.parser')
    host = urlsplit(http.url).hostname
    #return [url + '/' + node.get('href') for node in soup.find_all('a') if urlsplit(node.get('href')).hostname == host]
    seen = set()

    for node in soup.find_all('a'):
        href = node.get('href')
        if href is None:
            continue
        url = urlsplit(href)
        path = url.path

        if path in seen:
            continue

        seen.add(path)
        if url.hostname == host or not url.hostname:
            yield url.path 

def http_srcs(http):
    soup = BeautifulSoup(http.text, 'html.parser')
    host = urlsplit(http.url).hostname
    #return [url + '/' + node.get('href') for node in soup.find_all('a') if urlsplit(node.get('href')).hostname == host]
    seen = set()

    for node in soup.find_all('img'):
        src = node.get('src')
        if src is None:
            continue
        url = urlsplit(src)
        path = url.path

        if path in seen:
            continue

        seen.add(path)
        if url.hostname == host or not url.hostname:
            yield url.path 



def http_path2path(http,path):
    """ take a ftp connection and a path return the true path 
    if path is an url or path. 
    If the url hostanme or login is different than 
    """
    url = urlsplit(path)
    http = http.url
    if not url.hostname:
        return path
    if url.hostname!=ftp.hostname:
        raise ValueError("connection mismatch : '%s', '%s'"%(url.hostname, ftp.hostname))

    #if url.username and url.username!=getattr(ftp,"username", url.username):
    #   raise ValueError("connection username mismatch : '%s', '%s'"%(url.username, ftp.username))
    return url.path[1:] # remove the root '/'



def _http_dir(http, pathes, pref, output):
    
    if not len(pathes):
        try:
            lst = [pref] if pref and (len(ftp.nlst(pref)) or _ftp_exists(ftp, pref))  else []
            ## if below line uncomment it will end up with a one depth more 
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




