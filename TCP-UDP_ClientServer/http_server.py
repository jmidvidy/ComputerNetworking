# -*- coding: utf-8 -*-
"""
EECS 340, Fall 2018
Project 1 : http_server.py 

Part 2: A simple web server

@author: Jeremy Midvidy
@version: Python 2.7
"""

import socket
import sys
import os

##################################
# --------- DEV NOTES ---------- #
# add comments before functions
# make sure to remove print statements
# make sure to change path to argv
##################################

# transform recieved message to readable type
def processMessage(res):
    out = [] # < -- construct list of strings from res
    curr = ""
    for line in res:
        if line == "\n": # <- akin to splitting along "\n"
            out.append(curr)
            curr = ""
        else:
            curr += line
    return out

def makeResponse(code):
    error_phrase = "Not Found"
    if code == 200:
        error_phrase = "OK"
    elif code == 403:
        error_phrase = "Forbidden"
    error_message = ""+ str(code) + " " + error_phrase
    header = "HTTP/1.1 " + error_message + "\r\n\r\n"
    return header
    
def makeHTMLBody(code, path):
    # if code == 200; return HTML body
    if code == 200:
        with open(path,'r') as f:
            out = f.read()
        return out
    # if code == 403; return HTML body wtih : 403 Forbidden     
    if code == 403:
        return ("""<html><body><h1>Error 403: Forbidden</h1></body></html>""")
    # if code == 404; return HTML body with: 404 File Not Found
    if code == 404:
        return ("""<html><body><h1>Error 404: File Not Found</h1></body></html>""")
    return

def checkPath(path, path_ending):
    # fetch current directory and process header requests
    curr_dir = os.listdir('.')
    print(path_ending)

    # see whether file exists in the current directory
    file_exists = False
    if path in curr_dir:
        file_exists = True
    
    #see whether the file 
    good_ending = False
    if path_ending == ".html" or path_ending == ".htm":
        good_ending = True
    
    return file_exists, good_ending

def main(port):
    # instantiate TCP server with inputted port
    sS = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sS.setblocking(3)
    sS.bind(('',port)) # <-- '' allows listening from all IPS
    sS.listen(5) # set back log to 3
    print("The server is ready to recieve on port " + str(port) + "!")
    while True:
        # --- listen, acceot, and process message --- #
        connectionSocket, addr = sS.accept()
        message = connectionSocket.recv(1024).decode()
        message = processMessage(message)
        run = True
        # --- extract header, path, and end of path --- #
        try:
            header = message[0]
            print("\n")
            print(header)
            path = header[header.index(' ')+1:]
            path = path[:path.index(' ')]
            path = path[1:] #knock off '/' from lead
            path_ending = path[path.index('.'):]
            print(path)
        except: #badly formatted input string
            print("Badly formatted path!")
            response = makeResponse(404)
            connectionSocket.send(response.encode())
            body = makeHTMLBody(404, "")
            connectionSocket.send(body)
            connectionSocket.close()
            run = False
        
        if run == True:
            # --- helper to see if given path is in the current dir and has good ening --- #
            file_exists, good_ending = checkPath(path, path_ending)
            
            # --- check file_exists and good_ending, configure response with correct response code --- #
            # file is in the current directory and has a good ending
            code = 404 # file does not exist
            if file_exists and good_ending:            
                code = 200
                
            # file is in the current directory but does not end in ".html, .htm"
            elif file_exists:
                code = 403
                   
            # GATHER response message and send to connection socket
            response = makeResponse(code) 
            connectionSocket.send(response.encode())
            
            # GATHER response body and send to connection socket
            body = makeHTMLBody(code, path)
            if code == 200:
                body = body.encode()
            connectionSocket.send(body)
            
            # close connection socket
            connectionSocket.close()

        # reset run to true on each new iteration
        run = True
    return
    
if __name__ == "__main__":
    try:
        port = int(sys.argv[1])
    except:
        port = -1
    # can't use port 80
    # ports less than the 1024 are reserved on my machine
    #port = 5000 # <--- port is the single command line argument
    if port == -1:
        print("Error: No valid port number passed.  Please try again with a valid port number.")
    elif port < 1024:
        print("Error: Port number is too low.  Please use port 1024 or greater.")
    else:
        main(port)
