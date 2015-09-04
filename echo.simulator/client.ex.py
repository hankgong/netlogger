#!/usr/bin/env python

"""
An echo client that uses UDP.  Entering a blank line will exit the client.
"""

import optparse
import select
import socket
import sys

# setup variables
size = 1024

# parse options
parser = optparse.OptionParser(usage = "%prog [options]",
                               version = "%prog 0.1")
parser.add_option("-p", "--port", type="int",dest="port",
                  metavar="PORT",default=0,
                  help="port number for the server")
parser.add_option("-s", "--server", type="string", dest="host",
                  metavar="SERVER",default=socket.gethostname(),
                  help="host name for the server")
parser.add_option("-d","--debug",action="store_true",dest="debug",
                  default=False,
                  help="print debugging information") 

(options, args) = parser.parse_args()

host = options.host
port = options.port
debugging = options.debug


# setup socket
client = None
try:
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error, (code,message):
    if client:
        client.close()
    print "Could not open socket: " + message
    sys.exit(1)
    
    
sys.stdout.write('%')
sys.stdout.flush()

# handle input
input = [client,sys.stdin]
running = True
while running:
    inputready,outputready,exceptready = select.select(input,[],[]) 

    for s in inputready:
        
        if s == client:
            try:
                data,address = client.recvfrom(size)
            except socket.error, (code,message):
                print "Error: socket broken: " + message
                break
            sys.stdout.write(data)
            sys.stdout.write('%')
            sys.stdout.flush()
        elif s == sys.stdin:
            line = sys.stdin.readline()
            if line == '\n':
                running = False
            try:
                client.sendto(line,(host,port))
            except socket.error, (code,message):
                print "Error: socket broken: " + message
                break
            sys.stdout.write('%')
            sys.stdout.flush()  

# close socket
s.close()