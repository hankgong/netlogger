#!/usr/bin/env python

"""
A simple echo server that uses UDP
"""

import optparse
import select
import socket
import sys

# setup variables
host = "127.0.0.1"
backlog = 5
size = 1024 

# parse options
parser = optparse.OptionParser(usage = "%prog [options]",
                               version = "%prog 0.1")
parser.add_option("-p", "--port", type="int",dest="port",
                  metavar="PORT",default=0,
                  help="port number for the server")
parser.add_option("-d","--debug",action="store_true",dest="debug",
                  default=False,
                  help="print debugging information") 

(options, args) = parser.parse_args()

port = options.port
debugging = options.debug

# create socket
server = None
try:
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((host,port))
    print server.getsockname()
except socket.error, (code,message):
    if server:
       server.close()
    print "Could not open socket: " + message
    sys.exit(1)

# loop through sockets
input = [server,sys.stdin]
running = True
while running:
    inputready,outputready,exceptready = select.select(input,[],[]) 

    for s in inputready: 

        if s == server:
            # handle the server socket
            try:
                data,address = server.recvfrom(size)
                print data
                server.sendto(data,address)
            except:
                running = False 

        elif s == sys.stdin:
            # handle standard input
            junk = sys.stdin.readline()
            running = False

# close server socket
server.close()