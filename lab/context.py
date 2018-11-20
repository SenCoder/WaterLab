import logging
import threading
import time
import uuid
import os

from lab import adb
from lab.util import util
from lab.const import error
from lab.serial.cmd import SerialHelper
from lab.adb import Adb
# import lab.adb as adb

testOver = False


class RunContext(object):
    def __init__(self, ttyusb, ipAddr):
        self.serial = SerialHelper(ttyusb)
        self.ip = ipAddr
        self.appPkgName = ''
        self.testAppPkgName = ''
        self.appPath = ''
        self.testAppPath = ''
        self.sitafile = ''
        self.interval = 1
        # self.videoSignal = threading.Event()
        self.pullSignal = threading.Event()
        self.timeout = 30
        self.adb = Adb(ipAddr)

    def set_timeout(self, timeoutmin):
        self.timeout = timeoutmin

    def set_app_path(self, app_path, test_app_path):
        self.appPath = app_path
        self.testAppPath = test_app_path

    def set_sita_path(self, zip_file_path):
        self.sitafile = zip_file_path

    def set_pkg_name(self):
        self.appPkgName = util.pkg_name(self.appPath)
        self.testAppPkgName = util.pkg_name(self.testAppPath)

    def check_apk(self):
        logging.debug('checkApk')
        if self.testAppPkgName != self.appPkgName + '.test':
            util.exit_with_error(error.TEST_REPLY_FAIL_RUN)
        return True

    def adb_conn(self):
        ret = self.adb.connect()
        if ret == adb.ADB_FAIL_REFUSE:
            self.serial.run_cmd('start adbd')
            time.sleep(1)
            self.adb.connect()
        elif ret == adb.ADB_FAIL_UNABLE or ret == adb.ADB_FAIL_TIMEOUT:
            logging.info('adb_conn return False')
            return False
        check = self.adb.check()
        if check == adb.ADB_SUCCESS:
            return True
        else:
            for i in range(adb.ADB_CONN_MAX_NUM * 2):
                if check == adb.ADB_FAIL_OFFLINE or check == adb.ADB_FAIL_UNAUTHORIZED:
                    self.adb.reset()
                    check = self.adb.check()
                if i == adb.ADB_CONN_MAX_NUM and check == adb.ADB_FAIL_UNAUTHORIZED:
                    self.adb_auth()
            if check == adb.ADB_SUCCESS:
                return True
        logging.info('adb_conn return False')
        return False

    def adb_auth(self):
        adbKeyPath = os.environ['HOME'] + adb.ADB_KEY_PATH
        f = open(adbKeyPath)
        try:
            adbkey = f.read()
            print adbkey
            self.serial.run_cmd("echo \"" + adbkey + "\">> " + adb.ADB_KEY_PATH_BOARD)
            self.serial.run_cmd("chmod 640 " + adb.ADB_KEY_PATH_BOARD)
        finally:
            f.close()

    def make_report(self, result):
        logging.debug('make_report')
        name = str(uuid.uuid1()) + '.result'
        f = open(name, 'w')
        f.write(result)
        f.close()
        return name

    def make_reports(self, results):
        logging.debug('make_reports')
        name = str(uuid.uuid1()) + '.result'
        f = open(name, 'w')
        for item in results:
            f.write(item)
            f.write('\n')
        f.close()
        return name

    def video_record(self):
        t = threading.Thread(target=self.record)
        t.start()

    def record(self):
        index = 0
        records = []
        while not testOver:
            records.append("record" + str(index) + ".mp4")
            self.adb.run_adb_cmd("adb shell screenrecord --time-limit 20 /data/local/tmp/" + records[index], context=self)
            index += 1
        else:
            logging.info("video record over")
            for i in range(len(records)):
                newrecord = str(uuid.uuid1()) + ".mp4"
                self.adb.run_adb_cmd("adb pull /data/local/tmp/" + records[i] + " " + newrecord, context=self)
                records[i] = newrecord
        logging.info('video pull over')
        logging.info(records)
        util.merge_video(records)
        self.pullSignal.set()
