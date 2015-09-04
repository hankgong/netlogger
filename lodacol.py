#!/usr/bin/python
###################################################################################################
#    System:  CVG
#    Module:  LDC
# $Workfile:   lodacol.py $
#     $Date:   2014-07-03 19:23:33 GMT $
# $Revision:   \main\CVG_TLDC_Integration\13 $
####################################################################################################
# CONFIDENTIAL. All rights reserved. Thales Rail Signalling Solutions. This computer program is
# protected under Copyright. Recipient is to retain the program in confidence, and is not permitted
# to copy, use, distribute, modify or translate the program without authorization.
###################################################################################################
# Local Data Collector client
###################################################################################################

import optparse
import re
import fileinput
import string
import array
import os
import random
import struct
import socket
import select
import time
import datetime
import array
import base64
import io
import StringIO

ICD_VERSION = 2
TLDC_TIMEOUT = 6.0
FRAME_TYPE_DATA_SOLICITION =1
DEFAULT_ADDRESS = "192.168.200.3"
DEFAULT_PORT = 10000
POLL_RATE = 0.5

# Name of the optional environment variable where we look for files
APPVARS_DIR_ENV = 'APPVARS_DIR'

# Message Header
# 14 (time) + SwVer(3) + IntfBVer(1) + Length
HEADER = struct.Struct('<BBBBH')

# This Frame Length + Frame Type
FRAME_HEADER = struct.Struct('<HB')

DW_ATE_boolean = 0x2
DW_ATE_signed = 0x5
DW_ATE_signed_char = 0x6
DW_ATE_unsigned = 0x7
DW_ATE_unsigned_char = 0x8

class Configuration:
    def __init__(self, appid, cfgid, points):
        """
        Create a frame for data points
        """
        self.points = points
        self.appid = appid
        numpoints = len(points)
        # Set configid(1), appid(1) and number of points(2)
        frame = struct.pack('<BBH', cfgid, appid, numpoints)
        # Add variables
        for v_appid, v_name, v_addr, v_size, v_encoding in points:
            # address (4) + size(1)
            var = struct.pack('<LB', v_addr, v_size)
            frame = frame + var

        # pack this into a message frame (length is +1 because includes the frame_type)
        frame_type = FRAME_TYPE_DATA_SOLICITION
        frame = struct.pack('<HB', 1 + len(frame), frame_type) + frame
        # turn the frame into an array
        self.frame = array.array('c', frame)


class LocalDataCollector:
    """
    Extracts variables from target.
    """
    def __init__(self):
        self.allpoints = []
        self.request_mode = "one"
        self.target = (DEFAULT_ADDRESS, DEFAULT_PORT)
        self.version = (1, 0, 0)
        self.recv_buffer = array.array('c', 65536 * '\0')
        self.startup_poll = 0.0;
        self.cfgid = 1
        self.show_datapush = 0
        
    def add_config_from_file(self,  filename):
        """
        Add variables from an appvar file
        """
        fn = filename

        search_dir = os.getenv(APPVARS_DIR_ENV)
        if (not search_dir is None) and (-1 == fn.find('/')):
            fn = os.path.join(search_dir, fn)
        
        # if filename does not contain slashes and APPVARS_DIR is set
        # append the path
        with open(fn) as f:
            for line in f:
                (v_appid, v_name, v_addr, v_size, v_encoding) = string.split(line)
                v_appid = int(v_appid)
                v_addr = int(v_addr, 16)
                v_size = int(v_size, 10)
                v_encoding = int(v_encoding, 10)
                self.allpoints.append((v_appid, v_name, v_addr, v_size, v_encoding))

    def set_startup_poll(self, startup_poll):
        self.startup_poll = startup_poll;
        
    def __prepare(self):
        """
        Create configurations from self.allpoints
        Prepare Modes:
        - 'all' All points are mixed together into one configuration request
        Used mostly for testing the behaviour with real data collector
        - 'one'  Creates one configuration for each application.
        This is the default in the lab and most performant mode. 
        Used to replace old diagnostics.
        """

        self.config_frames = []
        self.configs = {}
        #
        # Create a configuration message for each application id
        #
        cfgs_by_app = {}

        # group by appid
        for  v_appid, v_name, v_addr, v_size, v_encoding in self.allpoints:
            if cfgs_by_app.has_key(v_appid):
                cfgs_by_app[v_appid].append((v_appid, v_name, v_addr, v_size, v_encoding))
            else:
                cfgs_by_app[v_appid]=[(v_appid, v_name, v_addr, v_size, v_encoding)]

#        for v_appid, v_name, v_addr, v_size in cfgs_by_app[2]:
#            print hex(v_addr)

        # create a config per appid
        cfgid  = self.cfgid

        for appid in cfgs_by_app.keys():            
            self.configs[cfgid] = Configuration(appid, cfgid, cfgs_by_app[appid])
            cfgid = cfgid + 1

        if self.request_mode == 'all':
            # will create pack all configs into one message
            all_configs_frame = array.array('c')
            all_points = []
            for c in  self.configs.itervalues():
                all_configs_frame = all_configs_frame + c.frame
            num_messages = len(self.configs)
            # create a frame with no_message + all config frames
            all_configs_frame = array.array('c', struct.pack('<B', num_messages)) + all_configs_frame
            # add the header
            all_configs_frame = array.array('c', HEADER.size * '\0') + all_configs_frame
            # this is the only frame we put in self.config_frames
            self.config_frames.append(all_configs_frame)
        elif self.request_mode == 'one':
            for c in  self.configs.itervalues():
                num_messages = 1
                # create a frame with 1 message
                oneframe = array.array('c', struct.pack('<B', num_messages)) + c.frame
                # add the header
                oneframe = array.array('c', HEADER.size * '\0') + oneframe
                # this is the only frame we put in self.config_frames
                self.config_frames.append(oneframe)
            

        # poll message has 1 byte payload ( num messages = 0)
        self.poll_message = array.array('c', (HEADER.size + 1) * '\0')


    def set_request_mode(self, request_mode):
        """
        request_mode = 'one' => All config requests are sent sepparate
        request_mode = 'all' => All config requests are packed in one frame
        """
        allowed_request_modes = ['one', 'all']
        if request_mode in allowed_request_modes:
            self.request_mode = request_mode
        else:
            raise Exception("Invalid request mode should be one of " + str(allowed_request_modes))


    def run(self):
        """
        Implements the dialog with target data collector
        """

        self.__prepare()

        if not self.config_frames:
            raise "No configurations found"


        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        startup_poll = self.startup_poll
        if startup_poll > 0.0:            
            self.__send_poll(s)

        while startup_poll > 0.0:
            t0 = time.time() 
            (r, w, x) = select.select([s], [], [], POLL_RATE)
            t1 = time.time()
            if r:
                # received a message
                n = s.recv_into(self.recv_buffer)
                self.__process_recv_buffer(n)
                if t1 - t0 > 0.0:
                    select.select([], [], [], t1 - t0)
            else:
                # cancel timeout
                t0 = t1
                self.__send_poll(s)
            startup_poll = startup_poll - POLL_RATE


        self.__send_config_request(s)
        #t0 = time.time() + TLDC_TIMEOUT
        self.__dump_headers()

        timeout = POLL_RATE
        havedata = 0
        while 1:
            try:
                t0 = time.time()
                (r, w, x) = select.select([s], [], [], timeout)
                t1 = time.time()
                timeout = timeout - (t1 - t0)
                if r:
                    n = s.recv_into(self.recv_buffer)
                    n = self.__process_recv_buffer(n)
                    if n:
                        havedata = 1

                if timeout <= 0.0:
                    timeout = POLL_RATE
                    if havedata:
                        self.__send_poll(s)
                    else:
                        self.__send_config_request(s)
                    havedata = 0
                    
            except:
                raise
                s.close()
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                timeout = POLL_RATE

        pass
        
  
    def run_static(self):
        """
        Implements the dialog with target data collector
        """

        self.__prepare()


        timeout = POLL_RATE
        
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        while 1:
            t0 = time.time()
            (r, w, x) = select.select([s], [], [], timeout)
            t1 = time.time()

            timeout = timeout - (t1 - t0)

            if r:
                # received a message
                n = s.recv_into(self.recv_buffer)
                self.__process_recv_buffer(n)

            if timeout <= 0.0:
                self.__send_poll(s)
                timeout = POLL_RATE


    def __process_recv_buffer(self, n):
#        print "received %d bytes"%(n)
        
        # Message format
        # Header = 20 bytes
        # Num Messages = 1 byte (always 1)
        #
        # One message
        #
        # Frame Len = 2 bytes (includes frame type)
        # Frame Type = 1 byte
        # Configuration Identifier = 1 byte
        # Variables
        #
        
        #print  base64.b16encode(self.recv_buffer[0:n])
        if n < HEADER.size:
            return 0
        (vMajor, vMinor, vPatch, vICD, size) = HEADER.unpack_from(self.recv_buffer, 0)
        if not size:
            return 0
        num_msgs = ord(self.recv_buffer[HEADER.size])
        if not num_msgs:
            return 0

        (fLen, fType ) = FRAME_HEADER.unpack_from(self.recv_buffer, HEADER.size + 1)


        if fType == 0xff:
            if self.show_datapush:
                print  base64.b16encode(self.recv_buffer[0:n])
            return 0
        
        cfg_id = ord(self.recv_buffer[HEADER.size + 4])
        

        c = self.configs[cfg_id]
        s = StringIO.StringIO()

        s.write(str(c.appid))

        data_start = HEADER.size + 5

        for v_appid, v_name, v_addr, v_size, v_encoding in c.points:
            s.write(',')

            enc = 1
            fmt = ""
            if v_encoding == DW_ATE_boolean:
                fmt = "<i"
            elif v_encoding == DW_ATE_signed and v_size == 1:
                fmt = "<b"
            elif v_encoding == DW_ATE_signed and v_size == 2:
                fmt = "<h"
            elif v_encoding == DW_ATE_signed and v_size == 4:
                fmt = "<i"
            elif v_encoding == DW_ATE_signed_char:
                fmt = "<b"
            elif v_encoding == DW_ATE_unsigned and v_size == 1:
                fmt = "<B"
            elif v_encoding == DW_ATE_unsigned and v_size == 2:
                fmt = "<H"
            elif v_encoding == DW_ATE_unsigned and v_size == 4:
                fmt = "<I"
            elif v_encoding == DW_ATE_unsigned_char:
                fmt = "<B"
            else:
                enc = 0

            if enc:
                (value,) = struct.unpack_from(fmt, self.recv_buffer, data_start)
                s.write(str(value))
                
            if not enc:
                if v_size == 1:
                    (value,) = struct.unpack_from("<B", self.recv_buffer, data_start)
                    s.write(str(value))
                elif v_size == 2:
                    (value,) = struct.unpack_from("<h", self.recv_buffer, data_start)
                    s.write(str(value))
                elif v_size == 4:
                    (value,) = struct.unpack_from("<L", self.recv_buffer, data_start)
                    s.write(str(value))
                else:
                    s.write(base64.b16encode(self.recv_buffer[data_start:data_start+v_size]))
            data_start = data_start + v_size
        print s.getvalue()

        # sanity check
        datalen = data_start - (HEADER.size + 5)
        if datalen <> fLen - 2:
            raise Exception("Invalid frame %d %d"%(datalen, fLen))
        return 1

    def __dump_headers(self):
        for cfgid in self.configs.keys():
            print self.__get_config_csvheader(cfgid)

    def __get_config_csvheader(self, cfgid):
        c = self.configs[cfgid]        
        hdr = "AppId%d"%(c.appid)
        
        for v_appid, v_name, v_addr, v_size,v_encoding in c.points:
            hdr = hdr + ",%s"%(v_name)
        return hdr
    
    def __send_config_request(self, s):
        """
        Send config request to target.
        """

        for c in self.config_frames:
            self.__update_header(c)
            s.sendto(c, 0, self.target)
            #print "[C]" , base64.b16encode(c)
    def __send_poll(self, s):
        """
        Send poll message to target
        """
        self.__update_header(self.poll_message)
        s.sendto(self.poll_message, 0, self.target)
        #print "[P]" , base64.b16encode(self.poll_message)

    def __update_header(self, abuffer):
        size = len(abuffer) - HEADER.size
        HEADER.pack_into(abuffer, 0, self.version[0], self.version[1], self.version[2], ICD_VERSION, size)

if __name__ == "__main__":
    parser = optparse.OptionParser("./lodacol.y options VARFILE ...")

    parser.add_option("-r", "--request-mode", dest="request_mode", action="store", help="""
If request-mode = 'all' All configuration requests are packed in one frame
If request-mode = 'one' Each configuration is requested in a sepparate frame.
By default should be one.
""")

    parser.add_option("-t", "--target", dest="target", action="store", help="""Target IP address.
The port is optional and if specified mult follow a semicolon (Ex: 127.0.0.1:58822)
""")

    parser.add_option("-c", "--config-id", dest="cfgid", action="store", help="""
All configuration request have an identifier. When using many instances it is neccesary
to have a unique config request, otherwise the other client requests will be wiped out.
""")
    parser.add_option("-p", "--startup-poll", dest="startup_poll", action="store", help="""
    This is for testing only. When set it will start the communication by sending empty poll messages
    for a number of seconds specified in the argument at 0.5 second interval.
    """)

    parser.add_option("-s", "--static-mode", dest="static_mode", action="store_true", help="""
Work in data push mode. Will poll VOBC only and display raw frames.
""")

    parser.add_option("-e", "--show-datapush", dest="show_datapush", action="store_true", help="""
Work in data push mode. Will poll VOBC only and display raw frames.
""")    
    
    (options, args) = parser.parse_args()

    ldc = LocalDataCollector()

    # Check if there are files 
    files = []
    if parser.largs:
        # .var files are part of command line
        files = parser.largs
    else:
        # Try to look for files in 'APPVARS_DIR' folder
        search_dir = os.getenv(APPVARS_DIR_ENV)
        if not search_dir:
            search_dir = '.'

        r = re.compile('.*?[.]var$', re.I)
        for fn in os.listdir(search_dir):
            cfgfn = os.path.join(search_dir, fn)
            if os.path.isfile(cfgfn):
                m = r.match(cfgfn)
                if m:                    
                    files.append(cfgfn)
    
    for fn in files:
        ldc.add_config_from_file(fn)
        
    if options.startup_poll:
        ldc.set_startup_poll(float(options.startup_poll))
        
    if options.request_mode:
        ldc.set_request_mode(options.request_mode)
        
    if options.cfgid:
        ldc.cfgid = int(options.cfgid)

    
    if options.target:
        tmp = options.target.split(":")
        target = tmp[0]
        port = DEFAULT_PORT
        if len(tmp) > 1:
            port = int(tmp[1])
        ldc.target = (target, port)

    if options.show_datapush:
        ldc.show_datapush = 1

    if options.static_mode:
        ldc.run_static()
    else:
        ldc.run()

    

