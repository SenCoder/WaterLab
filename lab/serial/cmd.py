# coding=utf-8
import logging
import re
import time
import serial

import cmd
from lab.util import LOGCAT, logcatpid, logcatfile


class SerialHelper(object):
    def __init__(self, ttyusb):
        self.ttyusb = ttyusb

    def admin(self):
        self.run_cmd('su')
        self.run_cmd('tclsu')

    def read_start_label(self):
        time.sleep(30)
        # result = False
        # sess = serial.Serial("/dev/" + self.ttyusb, baudrate=115200, timeout=1)
        # startTime = time.time()
        # while time.time() - startTime < 10:
        #     msg = sess.readline()
        #     if 'Starting kernel' in msg:
        #         result = True
        #         break
        # sess.close()
        # return result

    # if serial port is used by other process, wait to timeout
    def run_cmd(self, cmd):
        msg = ""
        sess = serial.Serial("/dev/" + self.ttyusb, baudrate=115200, timeout=5)
        try:
            sess.write('su' + "\r")
            msg = sess.read_until(terminator='#')
            sess.write('tclsu' + "\r")
            msg = sess.read_until(terminator='#')
            sess.write(cmd + "\r")
            msg = sess.read_until(terminator='#')
            self.err_handle(sess, msg)
        except serial.serialutil.SerialException:
            logging.debug('Serial Error')
        else:
            sess.close()
        logging.info(msg)
        return msg

    def get_ip(self):
        # msg = self.run_cmd('getprop dhcp.eth0.ipaddress')
        msg = self.run_cmd('ifconfig eth0')
        ipmatch = r'(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)'
        matches = re.findall(ipmatch, msg)
        count = 60
        while len(matches) <= 0 < count:
            count -= 1
            time.sleep(2)
            if count % 2 == 1:
                msg = self.run_cmd('ifconfig eth0')
            else:
                msg = self.run_cmd('busybox ifconfig eth0')
            logging.debug(msg)
            matches = re.findall(ipmatch, msg)
        else:
            if count == 0:
                return ""
            return matches[0]

    def get_software_version(self):
        msg = self.run_cmd('getprop ro.software.version_id')
        matches = re.findall('(?:[0-9A-Z]+\-){2}[0-9A-Z]+', msg)
        if len(matches) > 0:
            return matches[0]
        return ''

    def get_hardware_version(self):
        msg = self.run_cmd('getprop ro.hardware.version_id')
        matches = re.findall('[A-Za-z]+[0-9]+', msg)
        if len(matches) > 0:
            return matches[0]
        return ''

    def get_mac(self):
        msg = self.run_cmd('ifconfig eth0')
        matches = re.findall(r'(?:[\da-fA-F]{2}:){5}[\da-fA-F]{2}', msg)
        if len(matches) > 0:
            return matches[0]
        return ''

    def get_clientype(self):
        msg = self.run_cmd('cat /data/devinfo.txt')
        matches = re.findall('TCL[0-9A-Z\-]+', msg)
        if len(matches) > 0:
            return matches[0]
        return ''

    # 检验是否成功启动
    def check_device_on(self):
        self.read_start_label()
        ip = self.get_ip()
        if len(ip) > 0:
            return True
        return False

    def start_logcat(self):
        self.run_cmd("logcat -c")
        self.run_cmd("rm -f " + LOGCAT)
        msg = self.run_cmd("logcat -f " + LOGCAT + " &")
        matches = re.findall('\[\d*\] \d*', msg)
        if len(matches) > 0:
            cmd.logcatpid = int(matches[0].split(' ')[1])

    def stop_logcat(self):
        if logcatpid > 0:
            self.run_cmd('kill ' + str(logcatpid))
        else:
            msg = self.run_cmd('pgrep logcat')
            matches = re.findall('\d+', msg)
            if len(matches) > 0:
                pid = matches[0]
                logging.debug('logcat pid = ' + pid)
                self.run_cmd('kill ' + pid)
        return logcatfile

    def err_handle(self, sess, data):
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError('expected %s or bytearray, got %s' % (bytes, type(data)))
        if '>' in data:
            sess.write('\x03')
