# -*- coding: utf-8 -*-
"""
EECS 340, Fall 2018
Project 2, Part 2: UDP DNS proxy

@author: Jeremy Midvidy, jam658
"""
import socket

def main():
    # initalize incoming ip address and port
    port = 53
    
   # ip = '35.160.47.116' # localhost for testing
    upstream_ip = '8.8.8.8'
    upstream_port = 53
    
    # initialize UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # listen on port 53
    sock.bind(('', port))
    
    # wait for incoming messages
    print("Now listening for DNS queries on port 53!")
    while True:
        data, addr = sock.recvfrom(512)
        print("----------------------------------------------------")
        print("Recieved from: " + str(addr))
        print("Fetching upstream response")
        sock.sendto(data , (upstream_ip, upstream_port))
        response, addr2 = sock.recvfrom(512)
        print("Got upstream response from " + str(addr2))
        if data != response:
            print("Response good")
        #print(response)
        print("Sending response to " + str(addr))
        sock.sendto(response, addr)
        print("-----------------------------------------------------")
    return

if __name__ == '__main__':   
    main()
