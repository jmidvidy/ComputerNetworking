# -*- coding: utf-8 -*-
"""
EECS 340, Fall 2018
Project 2, Part 3: TCP DNS Proxy

@author: Jeremy Midvidy, jam658
"""
import socket
import select

def runTCP(e, ip, port):
    # open TCP socket from inputted e (tcps)
    tcp_socket, tcp_addr = e.accept()
    print("-----------------------------------------------------")
    print("In TCP!")
    tcp_data = tcp_socket.recv(1024)
    print("Recived from: " + str(tcp_addr))
    print("Launching upstream socket")
    # become client and send tcp_data upstream
    
    # create NEW TCP CLIENT to connect to UPSTREAM server
    upstream_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    upstream_tcp.connect((ip, port))
    
    print("Sending query upstream to Google DNS")
    upstream_tcp.send(tcp_data)

    # extract two byte length field <-- will have to do this at some point
    print("Recieved upstream response from Google DNS")
    
    # recieve from upstream
    # will need to access byte size of the DNS query to make this more dynamic
    response = upstream_tcp.recv(4096)
    
    print("Sending response downsteam to " + str(tcp_addr))
    # send response downstream
    tcp_socket.send(response)
    tcp_socket.close()
    upstream_tcp.close()
    print("-----------------------------------------------------")
    return


def runUDP(e, ip, port):
    udp_data, udp_addr = e.recvfrom(512)
    print("-----------------------------------------------------")
    print("In UDP!")
    print("Recieved from: " + str(udp_addr))
    print("Fetching upstream response")
    e.sendto(udp_data , (ip, port))
    response, addr2 = e.recvfrom(512)
    print("Got upstream response from " + str(addr2))
    if udp_data != response:
        print("Response good")
    print(response)
    print("Sending response to " + str(udp_addr))
    e.sendto(response, udp_addr)
    print("-----------------------------------------------------")
    return

def main():
    # initalize incoming ip address and port
    port = 53
    
   # ip = '35.160.47.116' # localhost for testing
    upstream_ip = '8.8.8.8'
    upstream_port = 53
    
    # initialize UDP socket and TCP socket
    udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tcps = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # listen on port 53
    udps.bind(('', port))
    tcps.bind(('', port))
    tcps.listen(5)
    tcps.setblocking(0)
    udps.settimeout(1)
    tcps.settimeout(1)
    
    # change back to while True before submitting
    # wait for incoming messages
    print("Now listening for UDP and TCP DNS queries on port 53!")
    while True:
        ready, dis1, dis2 = select.select([udps, tcps], [], [])
        for e in ready:
            if e == tcps:
                runTCP(e, upstream_ip, upstream_port)
            elif e == udps:
                runUDP(e, upstream_ip, upstream_port)
    return

if __name__ == '__main__':   
    main()
