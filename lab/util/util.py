# coding=utf-8
import commands
import logging
import os
import sys
import uuid

import lab
from lab.const import error

# result label
RESULT_START_LABEL = '== water:1 =='
RESULT_END_LABEL = '== water:0 =='

cpuinfo = str(uuid.uuid1()) + "_cpuinfo.txt"
meminfo = str(uuid.uuid1()) + "_meminfo.txt"

recordfile = str(uuid.uuid1()) + ".mp4"

LOGCAT = '/data/local/tmp/logcat'

logcatpid = 0
logcatfile = str(uuid.uuid1()) + ".log"


def usage():
    print 'Usage: ./water.py Command [Command Args]\n'
    print 'Commands:'
    print '  init\t\t <serial-port> <ipaddr> <apk> <testapk>'
    print '  install\t <serial-port> <ipaddr> <apk> <testapk>'
    print '  run\t\t <serial-port> <ipaddr> <apk> <testapk> <interval>'
    print '  reset\t\t <serial-port> <ipaddr> <apk> <testapk>'
    print '  app\t\t <serial-port> <ipaddr> <apk> <testapk> <timeout>'
    print '  monkey\t <serial-port> <ipaddr> <apk> <interval>'
    print '  info\t\t <serial-port> <ipaddr>'
    print '  mid\t\t <serial-port> <ipaddr> <middle-dir>'
    print '  system\t <serial-port> <ipaddr> <soft.zip>\n'


def check_param(args):
    if len(args) <= 2:
        usage()
        exit_with_error(error.TEST_REPLY_FAIL_WRONG_CMD)
    if args[1] in lab.options:
        if args[1] == 'mid' and len(args) != 5:
            exit_with_error(error.TEST_REPLY_FAIL_WRONG_CMD)
        if args[1] == 'monkey' and len(args) != 6:
            exit_with_error(error.TEST_REPLY_FAIL_WRONG_CMD)
        if args[1] == 'app' and len(args) != 7:
            exit_with_error(error.TEST_REPLY_FAIL_WRONG_CMD)
    elif args[1] == 'info':
        pass
    else:
        exit_with_error(error.TEST_REPLY_FAIL_WRONG_CMD)


def exit_with_error(errCode, desc=""):
    logging.info(desc)
    if errCode == error.TEST_REPLY_FAIL_WRONG_CMD:
        usage()
    print RESULT_START_LABEL
    print 'Type=Task'
    print 'Code=' + str(errCode)
    if desc != "":
        print 'Description=' + error.get_desc_by_code(errCode) + ":" + desc
    else:
        print 'Description=' + error.get_desc_by_code(errCode)
    print ''
    print ''
    print 'Logs=' + logcatfile
    print RESULT_END_LABEL
    # os._exit(0)
    # os._exit 退出父进程无法获得脚本输出
    sys.exit(0)


def exit_success(resultfile):
    print RESULT_START_LABEL
    print 'Type=Task'
    print 'Code=' + str(error.TEST_REPLY_SUCCESS)
    print 'Description=' + error.TEST_SUCCESS
    print 'Result=' + resultfile
    print 'Video=' + recordfile
    print 'Logs=' + logcatfile
    print 'CpuInfo=' + cpuinfo
    print 'MemInfo=' + meminfo
    print RESULT_END_LABEL
    sys.exit(0)


def exit_info(info):
    print RESULT_START_LABEL
    print 'Type=Info'
    print 'Code=' + str(error.TEST_REPLY_SUCCESS)
    print 'Description=' + error.TEST_SUCCESS
    for item in info:
        print item
    print RESULT_END_LABEL
    sys.exit(0)


def pkg_name(appPath):
    output = os.popen('aapt d badging ' + appPath).readlines()
    if len(output) == 0:
        exit_with_error(error.TEST_REPLY_FAIL_INSTALL)
    return output[0].split(' ')[1].split('=')[1][1:-1]


def merge_video(records):
    if len(records) == 0:
        return ''
    for i in range(len(records)):
        logging.debug(records[i])
        tsFile = name_without_suffix(records[i]) + '.ts'
        commands.getstatusoutput(
            'ffmpeg -i ' + records[i] + ' -vcodec copy -acodec copy -vbsf h264_mp4toannexb ' + tsFile)
        records[i] = tsFile
    commands.getstatusoutput(
        'ffmpeg -i "concat:' + '|'.join(records) + '" -acodec copy -vcodec copy -absf aac_adtstoasc ' + recordfile)
    for video in records:
        commands.getstatusoutput('rm -f ' + video)


def name_without_suffix(name):
    pieces = name.split('.')
    return '.'.join(pieces[:len(pieces) - 1])
