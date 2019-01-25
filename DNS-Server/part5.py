# -*- coding: utf-8 -*-
"""
EECS 340, Fall 2018
Project 2, Part 5: Advertisement Server

@author: Jeremy Midvidy, jam658
"""

import socket
import sys
import os
import select

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
    hostname = "NOTYETFOUND"
   # print("before loop", hostname)
    for line in out:
        line = str(line)
        print("testing line:", line)
        if "Host" in line:
            hostname = line
   # print("after loop", hostname)
#   arr = hostname.split(' ')
#   hostname = arr[1]
#   if "\r" in hostname:
#     hostname = hostname[:hostname.index("/r")]
    return out, hostname

def makeResponse(code):
    error_phrase = "Not Found"
    if code == 200:
        error_phrase = "OK"
    elif code == 403:
        error_phrase = "Forbidden"
    error_message = ""+ str(code) + " " + error_phrase
    header = "HTTP/1.1 " + error_message + "\r\n\r\n"
    return header
    
def makeHTMLBody(code, hostname):
    a = hostname.decode("unicode-escape")
    arr = ""
    for c in a:
        arr += str(c)
    arr = arr[:len(arr)-1].strip()
    try:
        dar = arr.split(' ')[1]
    except:
        dar = "Couldn't Get Hostname"
    out =  ("<html><body><h1>Part 4: Advertisement Server</h1>" + 
           "<h2>Woops. You entered in: <strong>"+ dar +"</strong></h2>" +
           "<h2>I think you meant <a href=\"https://www.amazon.com/\">Amazon.com</a></h2>" + 
           "</body></html>")
    return out

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

def main_run(port, sock):         
    # --- listen, acceot, and process message --- #
    connectionSocket = sock
    message = connectionSocket.recv(1024).decode()
    message, hostname = processMessage(message)
    # --- extract header, path, and end of path --- #    
    # --- helper to see if given path is in the current dir and has good ening --- #
    code = 200
    # GATHER response message and send to connection socket
    response = makeResponse(code) 
    connectionSocket.send(response.encode())
    
    # GATHER response body and send to connection socket
    body = makeHTMLBody(code, hostname)
    if code == 200:
        body = body.encode()
    connectionSocket.send(body)
    
    # close connection socket
    connectionSocket.close()
    return

# main driver for http2_server.py
def main(port):    
    # initialize TCP acceptSocket, bind to inputted port
    acceptSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    acceptSocket.bind(('', port))
    #acceptSocket.setblocking(0)
    acceptSocket.listen(5)
    print("The server is ready to recieve on " + str(port) + "!")
    # initalize the list of open connections to empty and iterate repeatedly
    inputs = [acceptSocket]
    while True:
        readable, dis1, dis2  = select.select(inputs, [], [])
        for s in readable:
            if s == acceptSocket:
                sock, addr = acceptSocket.accept()
                sock.setblocking(0)
                inputs.append(sock)
            else:
                main_run(port,s)
                inputs.remove(s)
    return
    
if __name__ == "__main__":
    try:
        port = int(sys.argv[1])
    except:
        port = -1
    if port == -1:
        port = 80
    # can't use port 80
    # ports less than the 1024 are reserved on my machine
    #port = 5000 # <--- port is the single command line argument
    if port == -1:
        print("Error: No valid port number passed.  Please try again with a valid port number.")
    else:
        main(port)
