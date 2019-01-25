# -*- coding: UTF-8 -*-
"""
EECS 340, Fall 2018
Project 1 : http_client.py 

Part 1: A simple Curl Clone

@author: Jeremy Midvidy
@version: Python 2.7
"""

import socket
import urlparse
import sys
import copy 

# ---------- DEV NOTES ------------ #
# change path to sys.arv()
# change return to exit codes where needed
# COMMENT when everything is working well
# --------------------------------- #

def processURL(url):
    # -- CHECK if input url starts with "https://" --- #
    if url[:8] == "https://":
        print("Error: Inputted url attempts to access encrypted page (url starts with \'https://\')", "Inputted url: " + url)
        return 1,1,1
    
    # --- CHECK if input url starts with "http://" --- #
    if url[:7] != "http://":
        print("Error: Inputted url does not start with \'http://\'")
        return 1,1,1
    
    p = urlparse.urlparse(url)
    #print(p)
    
    host = p.netloc
    path = p.path
    
    # remove ending "/" if needed 
    if host[-1] == "/":
        host = host[:len(url)-1]
    
    # collect port if needed, adjust url to not contain port (I think that is correct)
    port = 80
    if host.find(':') != -1:
        ind = host.index(':')
        port = int(host[ind+1:])
        host = host[:ind]
                
    return host, path, port

def processResponse(s):
    out = [] # < -- construct list of strings from res
    curr = ""
    for line in s:
        if line == "\n": # <- akin to splitting along "\n"
            out.append(curr)
            curr = ""
        else:
            curr += line
    return out

def makeGET(request, host, port):
    
    # -- INIT socket, MAKE initial request, RECIEVE from client --- #
    # initalize clientSocket
    cS = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    recv_size = 10000
    
    # connect and configure port if url contains a port
    try:
        cS.connect((host, port))
    except:
        print("Error: Invalid URL")
        return 1
    
    # send request and recieve result
    cS.send(request)
    res = cS.recv(recv_size)
    
    # -- PROCESS result from client. -- #            
    out = processResponse(res)
    
    # check to see if byte of transmission is longer than recv_size
    cl = ""      
    for line in out:
        if "Content-Length:" in line:
            cl = line
            break
    
    # if long response, process remaning bytes and append to out
    long_response = ""
    if cl != "":
        content_length = cl.split(' ')[1]
        if "\r" in content_length:
            content_length = int(content_length.split("\r")[0])
        diff = recv_size - content_length
        if diff < 0:
            temp = copy.deepcopy(recv_size)
            while temp < content_length:
                long_response += cS.recv(recv_size)
                temp += recv_size
                
        long_out = processResponse(long_response)
        out.extend(long_out)
            
    return out

def writeRequest(path,host):
    if path == "":
        path = "/"
    if host[:4] == "www.":
        host = host[4:]
    return "GET " + path + " HTTP/1.0\r\nHost: " + host + "\r\n\r\n"


def callGET(url):
    # --- check to see if valid URL --- #
    host, path, port = processURL(url)
    if host == 1:
        return 1 #exit(1) #failure
    
    # format HTTP GET request
    request = writeRequest(path,host)
    #print(request)
    
    #print(request)
    response = makeGET(request, host, port)
    if response == 1:
        return 1 #exit(1) failure
    
    return response

# find location url for redirct codes
def findRedirect(r):
    for line in r:
        if "Location: " in line:
            return line[line.index(' ')+1:]
    return # error check if MUST have redirect

# print response body if content-type begins with "text/html"
def printResponse(r):
    val = ""
    pos = 0
    for i in range(0,len(r)):
        if "Content-Type" in r[i]:
            val = r[i]
            pos = i + 1
            break

    if "text/html" in val:
        for line in r[pos:]:
            print(line)
    else:
        return 1 #failure
    
    return 0 #success

# have exits here
def runHTTP(url):
    # stop redirects after 10
    redirects = 0
    # iterate until error, location found, 
    while True:
        response = callGET(url)
        if redirects > 9:
            print("Error: Too many redirects!", str(redirects) + " redirect calls made!")
            return 1 #update to exit(1) == failure
        if response == 1:
            return 1 #update to exit(1) 1 == failure
        
        header = response[0]
        print(header) #delete later
        code = header[header.index(' ')+1:]
        error_code = int(code[:code.index(' ')])
        
        # 200 OK
        if error_code == 200:
            res200 = printResponse(response) # std out if the content-type beigns with text/html.  Otherwise exit with non-zero code
            if res200 == 0:
                return 0 #success
            else:
                return 1 #failure
            
         
        # 301, 302 permanent redirect
        elif error_code == 301 or error_code == 302:
            new_url = findRedirect(response).replace('\r',"")
            redirects += 1
            print("Redirecting to: " + str(new_url))
            print("\n")
            url = new_url
            
        # error code is >= 400
        if error_code >= 400:
            printResponse(response)
            return 1
    return
        
def main(url):
    runResult = runHTTP(url)
    print("\n")
    if runResult == 0: #success
        print("SUCCESS: Returned exit code 0")
        sys.exit(0) #change to exit(0)
    else: #failure
        print("FAILURE: Returned exit code 1")
        sys.exit(1) #change to exit(1)

if __name__ == '__main__':
    try:
        path = sys.argv[1] # <--- remember to update
    except:
        path = -1
        
    path1 = "http://airbedandbreakfast.com" #301 permenant redirect
    path2 = "http://stevetarzia.com" #200 temp redirect
    path3 = "http://maps.google.com/" #302 temp redirect # <---- having problems here
    path4 = "http://maps.google.com/maps" #302 temp redirect <---- having problems here
    path5 = "http://stevetarzia.com/index.php" #302 temp redirect
    path6 = "http://stevetarzia.com/index" #200 OK
    path7 = "http://portquiz.net:8080/"
    path8 = "http://cs.northwestern.edu/340" #404 response code
    path9 = "http://stevetarzia.com/libc.html"
    path10 = "http://stevetarzia.com/redirect-hell" #too many redirects
    
    #path = path
    #path = "http://wedwedqcrerfqcwrcerfwecwedwefwefwef.py"
    # go through (1) allow requests to include a port number, (2) not require a slash at the end, 400 response codes etc
    if path == -1:
        print("\n")
        print("Error: No URL passed.  Please try again with a URL as a commnd line input.")
        print("FAILURE: Returned exit code 1")
        sys.exit(1)
    else:
        main(path)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

