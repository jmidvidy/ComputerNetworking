    # -*- coding: utf-8 -*-
"""
EECS 340, Fall 2018
Project 2, Part 4: Manipulated DNS

@author: Jeremy Midvidy, jam658
"""

import socket
import select
import binascii
import struct
import sys

# -------------------- PARSER ----------------------------------#
def makeQName(QFL):
    i = 0
    labels = []
    while i < len(QFL):
        labels.append(i)
        i = int(QFL[i], 16) + i + 1
    prev = labels[0]
    dar = []
    for i in labels[1:]:
        curr = QFL[prev+1:i]
        dar.append(curr)
    dar.append(QFL[labels[-1]+1:])
    par = []
    for elem in dar:
        curr = ""
        for c in elem:
            curr += binascii.unhexlify(c)
        par.append(curr)
    
    return '.'.join(par)


def parse(I, data, request, verbose):
    # convert a 0xAA byte to 8 length binary string
    A = []
    for line in I:
        v = hex(ord(line))[2:]
        if len(v) == 1:
            v = "0" + v
        A.append(v)
    
    # ---------------------------- EXTRACT HEADER ---------------------- #
    HF = A[0:12]
    Header = { 'ID' : [HF[0], HF[1]], 'FLAGS' : [HF[2], HF[3]], 'QDCOUNT': [HF[4], HF[5]], 
               'ANCOUNT': [HF[6], HF[7]], 'NSCOUNT': [HF[8], HF[9]], 'ARCOUNT': [HF[10], HF[11]]}
       
    # convert header to binary
    HeaderBin = {}
    for key in Header:
        curr = ""
        for elem in Header[key]:
            val = bin(int(elem, 16))[2:]
            if len(val) < 8:
                val = ("0" * (8 - len(val))) + val
            curr += val
        HeaderBin[key] = curr
        
    fb = HeaderBin["FLAGS"]
    Flags = {"QR": fb[0], "Opcode":fb[1:5] , "AA":fb[5] , 
             "TC":fb[6] , "RD":fb[7] , "RA":fb[8] , 
             "Z":fb[9:12] , "RCODE":fb[12:]}
    
    # know if QR = 1, then this is a DNS response
    QR = Flags["QR"]
    ERROR = Flags["RCODE"]
    AA = Flags["AA"]

    
    # ---------------------------- EXTRACT QUESTIONS -------------------- #
    q_end = 12
    while q_end < len(A):
        if A[q_end] == '00':
            break
        q_end += 1
    QF = A[12:q_end+5]
    QFL = A[12:q_end]  # Question_Field in the DNS query    
    Question_Labels = {'QNAME': 1,'QTYPE': [A[q_end+1], A[q_end+2]],'QCLASS': [A[q_end+3], A[q_end+4]]}
    qname = makeQName(QFL)   
    Question_Labels["QNAME"] = qname
    
    # short-circut if Resquest Packet
    if QR == "0":
        print("\tRequest Packet!")
        print("\tName: " + qname)
        return I, True
    
    # ---------------------------- EXTRACT ANSWER -------------------- #
    answer_start = q_end + 5
    #print(answer_start)
    #print(A[answer_start])
    AF = A[answer_start:]
    
    # UDP
    try:
        Answer = {"NAME": [AF[0], AF[1]], "TYPE": [AF[2], AF[3]], "CLASS": [AF[4], AF[5]],
              "TTL": [AF[6], AF[7], AF[8], AF[9]], "RDLENGTH": [AF[10], AF[11]], "RDLDATA": AF[12:]}
    # TCP truncated
    except:
        print("Truncated UDP Packet!")
        return I, True
        
    ans = Answer["RDLDATA"]
    dar = []
    for elem in ans:
        dar.append(str(int(elem, 16)))
    IP = ':'.join(dar)
    # ---------------------------- IF IP IS FALSE -------------------- #
    #verbose = 0
    if verbose == 1:
        if QR == '1':
            print("\tType: Response Packet!")
        else:
            print("\tType: Request Packet!")
        print("\tTransaction ID: " + hex(int(HeaderBin["ID"], 2)))
        if ERROR == '0000':
            print("\tno error: " + ERROR)
            if len(dar) == 4:
                print("\tIP: " + IP)
        else:
            print("\tERROR: " + ERROR)
            print("\tRerouting to " + manip_ip)
        if AA == "0":
            print("\tAA: Not Authorative Server")
        else:
            print("\tAA: Authorative Server")
        #print("\tDomain Name: " + qname)
        print("\tFlags: " + fb)
        
        ip_arr = manip_ip.split('.')
        ip_hex = ""
        for elem in ip_arr:
            curr = hex(int(elem))[2:]
            if len(curr) > 2:
                curr = curr[:2]
            ip_hex += curr
        print(ip_hex)
    
    
    # change DNS response to be manipulative for non-existant URL
    if ERROR != "0000":
        response = (data[0:3] +
                    binascii.unhexlify(str(int(binascii.hexlify(data[3]))-3)) +
                    data[4:6] + 
                    "\x00\x01\x00\x00\x00\x00" +
                    request[12:] + 
                    "\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x42\x00\x04" + 
                    binascii.unhexlify(ip_hex)) # HEX STRING TO BYTES --> USE UNHEXLIFY
                    #"\x23\xa0\x2f\x74")
        
        for elem in ip_hex:
            response = response + "\\x" + elem
        
        return response, False
    
    else:
        # don't change packet        
        return I, True

# ------------------------------------------------------------------------------------ # 
def getTCPSize(A):
    out = []
    for line in A:
        out.append(line)
    b = []
    for a in out:
        b.append(binascii.hexlify(a))
    sizeHEX = b[0] + b[1]
    size = int(sizeHEX, 16)
    print("size:" + str(size))
    return size, out

def processResponse(res, request):
    out = []
    for line in res:
        out.append(line)
    print("Packet Details:")
    print("Incoming Packet Hex:")
    b = ""
    for a in out:
        b += binascii.hexlify(a) + " "
    print(b)
    pack, isgood = parse(out, res, request, 1)
    if isgood == True:
            pack = res
    return pack, isgood


def runTCP(e, ip, port):
    # open TCP socket from inputted e (tcps)
    tcp_socket, tcp_addr = e.accept()
    print("-----------------------------------------------------")
    print("In TCP!")
    tcp_data = tcp_socket.recv(1024)
    print("Recived from: " + str(tcp_addr))
    print("Launching TCP upstream connection")
    # become client and send tcp_data upstream
    
    # create NEW TCP CLIENT to connect to UPSTREAM server
    upstream_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    upstream_tcp.connect((ip, port))
    
    print("Sending TCP packet upstream to Google DNS")
    upstream_tcp.send(tcp_data)

    # extract two byte length field <-- will have to do this at some point
    print("Recieved upstream response from Google DNS")
    
    # recieve from upstream
    # will need to access byte size of the DNS query to make this more dynamic
    init_response = upstream_tcp.recv(1096)
    size, curr_response = getTCPSize(init_response) # 10 byte buffer
    print("init size: " + str(len(curr_response)))
    while len(curr_response) < size:
        curr = upstream_tcp.recv(1096)
        init_response += str(curr)
        for line in curr:
            curr_response.append(str(line))
        
        print("update: " + str(len(curr_response)))
    
    response = init_response
    
    # need to parse response here
    
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
    print("Got upstream response from Google DNS at " + str(addr2))        
    pack, isgood = processResponse(response, udp_data)
    # if isgood, then do nothing
    # else, manipulate DNS
    if isgood == True:
        print("Response good")
        print("Sending response to " + str(udp_addr))
        e.sendto(pack, udp_addr)
    else:
        print("Response bad, manipualtive proxy will route to: " + manip_ip)
        e.sendto(pack, udp_addr)
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
    
    # change back to while True before submitting
    i = 1
    # wait for incoming messages
    print("Now listening for UDP and TCP DNS queries on port 53!")
    print("Will reroute bad proxies to: " + manip_ip)
    while True:
        #print(i)
        ready, dis1, dis2 = select.select([udps, tcps], [], [])
        for e in ready:
            if e == tcps:
                runTCP(e, upstream_ip, upstream_port)
            elif e == udps:
                runUDP(e, upstream_ip, upstream_port)
        i += 1
    return

if __name__ == '__main__':
    try:
        manip_ip = sys.argv[1]
    except:
        manip_ip = "35.160.47.116"
        print("No IP address given from command line, using my AWS EC2 IP4: " + manip_ip)
        #manip_ip = "123.123.123.123"

    main()
