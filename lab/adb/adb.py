# coding=utf-8
import commands
import logging
import re
import subprocess

import time
import os

from lab.util import util
from lab.const import error
from timeout import Timeout

ADB_CONN_MAX_NUM = 20
ADB_KEY_PATH = '/.android/adbkey.pub'
ADB_KEY_PATH_BOARD = '/data/misc/adb/adb_keys'

ADB_FAIL_REFUSE = "Connection refused"
ADB_FAIL_UNABLE = "unable"
ADB_FAIL_UNAUTHORIZED = "unauthorized"
ADB_FAIL_OFFLINE = "offline"
ADB_FAIL_TIMEOUT = "Connection timed out"
ADB_FAIL_UNKNOWN = "Unknown"
ADB_SUCCESS = "Success"


class Adb(object):
    def __init__(self, ipAddr):
        self.dev = ipAddr

    def connect(self):
        output = commands.getstatusoutput('adb connect ' + self.dev)
        logging.debug(output[1])
        if output[1].find(ADB_FAIL_REFUSE) >= 0:
            return ADB_FAIL_REFUSE
        elif output[1].find(ADB_FAIL_UNABLE) >= 0:
            return ADB_FAIL_UNABLE
        elif output[1].find(ADB_FAIL_TIMEOUT) >= 0:
            return ADB_FAIL_TIMEOUT
        return None

    def reset(self):
        logging.debug('adb reset')
        time.sleep(2)
        os.popen('adb disconnect ' + self.dev)
        time.sleep(1)
        os.popen('adb connect ' + self.dev)
        time.sleep(1)

    def check(self):
        output = os.popen('adb devices').readlines()
        for line in output:
            if line.find(self.dev) >= 0:
                if line.find('offline') >= 0:
                    return ADB_FAIL_OFFLINE
                elif line.find('unauthorized') >= 0:
                    return ADB_FAIL_UNAUTHORIZED
                else:
                    return ADB_SUCCESS
        return ADB_FAIL_UNKNOWN

    # 有卡死的可能，需要超时
    # 运行不能放串口执行命令，不知道何时测试执行完毕
    def run_cmd(self, cmd, timeout=None):

        cmd = 'adb -s ' + self.dev + ' ' + ' '.join(cmd.split(' ')[1:])
        logging.debug(cmd)

        if timeout is not None:
            cmd = cmd.split(' ')
            timer = Timeout(timeout)
            child = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)
            while child.poll() is None:
                if timer.expired():
                    logging.debug("adb.run_cmd expired")
                    child.kill()
                    child.wait()
                    break
            logging.debug("adb.run_cmd over")
            if child is not None and child.stdout is not None:
                output = child.stdout.readlines()
                output = ''.join(output)
                logging.debug(output)
                return output
            ret = "Failed Unknown"
            logging.debug(ret)
            return ret
        else:
            # shell=False 不能使用 >> 等重定向命令
            output = commands.getstatusoutput(cmd)
            logging.debug(output[1])
            return output[1]

    def run_adb_cmd(self, cmd, context, timeout=None):
        if self.check() != ADB_SUCCESS:
            if not context.adb_conn():
                logging.debug("run_adb_cmd fail because of adb connect fail.")
                util.exit_with_error(error.TEST_REPLY_FAIL_ADB)
        output = self.run_cmd(cmd, timeout)
        if output.find('error: device') >= 0 or output.find('adb: error') >= 0:
            logging.info('=== run_adb_cmd error because of adb exception')
            if context.adb_conn():
                logging.info('=== adb connect success, try to run_cmd again')
                output = self.run_cmd(cmd, timeout)
            else:
                logging.info('=== adb connect success, the program has to exit')
                util.exit_with_error(error.TEST_REPLY_FAIL_ADB)
        return output

    # 有卡死的可能，需要超时
    # 连接有断开的可能，若断开需要重连
    def install(self, apkfile, context):
        # 超时时间过长，部分平台会待机
        # E_help 84M, 300s too short
        output = self.run_adb_cmd('adb install -r ' + apkfile, context)
        # adb install 成功 5660 不会反馈 Success 信息 output.find('Success') < 0
        if len(output) <= 1 or output.find('Failure') >= 0 or output.find('Failed') >= 0 or output.find('disabled from pm') >= 0:
            matches = re.findall('\[[A-Z_]+\]', output)
            if len(matches) > 0:
                util.exit_with_error(errCode=error.TEST_REPLY_FAIL_INSTALL, desc=matches[0])
            util.exit_with_error(error.TEST_REPLY_FAIL_INSTALL)

    # 有卡死的可能，需要超时
    # 连接有断开的可能，若断开需要重连
    def uninstall(self, pkg, context):
        self.run_adb_cmd('adb uninstall ' + pkg, context)
