#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import serial
import struct

class BaseDriver:
    def __init__(self, params = dict()):
        self.__default_params = {"port" : "/dev/ttyUSB0",
                               "baud"  : 115200,
                               "timeout" : 0.1,
                               "data_cycle": 0.1,
                               "min_msg_len" : 5,
                               "header": [0x97],
                               "message_limit": 20,
                               "buffer_limit": 1000}

        for default_key in self.__default_params.keys():
            if(default_key not in params.keys()):
                params[default_key] = self.__default_params[default_key]

        self.port = params["port"]
        self.baud = params["baud"]
        self.timeout = params["timeout"]
        self.data_cycle = params["data_cycle"]

        self.min_msg_len = params["min_msg_len"]
        self.header = params["header"]
        self.message_limit = params["message_limit"]

        self.start_cycle_time = time.time()
        self.actual_cycle_time = 0

        self.state = 0
        self.rx_msg_cnt = 0
        self.error = 0
        self.first_msg = True
        
        self.buffer = list()
        self.__buffer_idx = 0

        self.header_buffer = [(0,0), (0,0)]

        self.disconnected = True

        while not self.check_connect():
            time.sleep(0.5)

    def check_connect(self):
        if(self.disconnected):
            self.first_msg = True
            
            try:
                self.ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
                print("Re-establish connection to the MCU")
                time.sleep(1)
                self.ser.flushInput()
                self.buffer = []
                self.__buffer_idx = 0
                self.disconnected = False
            except serial.serialutil.SerialException as e:
                return -1
        
        return 1

    def read1(self):
        if(self.check_connect() == -1):
            return -1

        try:
            data = self.ser.read(1)
        except IOError:
            self.ser.close()
            self.disconnected = True
            return (0, -1)

        if len(data):
            val = ord(data)
            self.buffer.append(val)
            self.__buffer_idx = len(self.buffer)-1
            return (1, val)
        return (0, 0)

    def readBytes(self, len, return_by_int = False):
        if(self.ser.in_waiting < len):
            return -1
        
        int_value = 0
        for i in range(len):
            if not self.read1()[0]:
                return (0, 0)

            if return_by_int == True:
                int_value <<= 8
                int_value |= self.buffer[self.__buffer_idx]

        if return_by_int == True:
            return (1, int_value) 
            
        return self.buffer[-len:]

    def readshort(self, return_by_int = False):
        return self.readBytes(2, return_by_int)

    def readlong(self, return_by_int = False):
        return self.readBytes(4, return_by_int)

    def readfloat(self):
        self.readBytes(4)
        return self.parseFloat()        

    def parseFloat(self, idx=None,):
        
        if(idx == None or idx > self._buffer - 3):
            idx = self.__buffer_idx-3

        value_byte = self.buffer[idx] << 24 | \
                     self.buffer[idx+1] << 16 | \
                     self.buffer[idx+2] << 8 | \
                     self.buffer[idx+3]
            
        value_byte_arr = bytearray(struct.pack("<I", value_byte))
        return struct.unpack(">f", value_byte_arr)[0]

    def readString(self):
        if(self.check_connect() == -1):
            return -1

        try:
            data = self.ser.readline().decode("utf-8")
        except IOError:
            self.ser.close()
            self.disconnected = True
            return ""
        return data[:-1]

    def default_data_callback(self, header, data):
        print("Message " + str(hex(header)) + ": " + str(hex(data)))
        return data

    def default_error_callback(self, error):
        return error

    def readMessage(self, data_len=4, error_cb=None, data_cb=None, data_cycle=None):
        if(self.check_connect() == -1):
            return -1

        if error_cb == None:
            error_cb = self.default_error_callback
        if data_cb == None:
            data_cb = self.default_data_callback
        if data_cycle == None:
            data_cycle = self.data_cycle

        # Wait the expected cycle time
        wait_retry = 0
        try:
            while(self.ser.in_waiting < (self.min_msg_len + data_len)):
                if(wait_retry >= 10):                
                    return -2
                time.sleep(data_cycle * 0.1)
                wait_retry += 1
        except IOError:
            self.ser.close()
            self.disconnected = True
            return -1


        self.actual_cycle_time = time.time() - self.start_cycle_time
        self.start_cycle_time = time.time()
        
        self.header_buffer[0] = self.header_buffer[1]
        self.header_buffer[1] = self.read1()

        if(self.header_buffer[0][0] and self.header_buffer[0][1] == 0x79 and self.header_buffer[1][1] in self.header):    
            rx_msg_cnt = self.read1()
            if(self.first_msg):
                self.rx_msg_cnt = rx_msg_cnt[1] - 1
                self.first_msg = False

            if(rx_msg_cnt[1] == (self.rx_msg_cnt + 1)&0xff):
                self.rx_msg_cnt += 1
            else:
                return -3

            self.state = self.read1()
            
            self.error = self.read1()
            error_cb(self.error)
            
            data = self.readBytes(data_len, True)
            if(data[0]):
                header = self.header_buffer[1][1]
                data_cb(header, data[1])

            if((self.rx_msg_cnt&0xff) % self.message_limit == 0):
                self.buffer = []
                self.__buffer_idx = 0

        return 0

        

    def __del__(self):
        if self.ser != None:
            self.ser.close()

if __name__ == "__main__":
    params = {"port" : "/dev/ttyUSB0", "header": [0x97, 0x96, 0x95], "data_cycle": 0.1}

    class TestDriver(BaseDriver):
        def __init__(self, params=dict()):
            BaseDriver.__init__(self, params)

            self.float_data = 0.0

            try:
                while True:
                    self.readString()
            except UnicodeDecodeError:
                pass            

        def data_callback(self, header, data):
            self.float_data = self.parseFloat()
            print("Message " + str(hex(header)) + ": " + str(self.float_data))
            print(len(self.buffer))
            
        def error_callback(self, error):
            print("Test pass method as argument")
            pass


    test = TestDriver(params)

    while True:        
        if(test.readMessage(4, data_cb=test.data_callback) == -1):
            if(test.disconnected == True):
                print("Lost connection with MCU")
            else:
                print("Error!")

