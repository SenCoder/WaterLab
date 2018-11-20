# coding=utf-8
import logging
import subprocess
import threading
import time
import uuid

import lab.context
from lab.const import error
from lab.util import util
from lab.util import cpuinfo, meminfo, logcatfile, LOGCAT

from nbstreamreader import NonBlockingStreamReader as NBSR


class BaseAgent(object):
    def __init__(self):
        self.context = None
        self.serial = None
        self.code = error.TEST_REPLY_SUCCESS

    def set_context(self, context):
        self.context = context
        self.serial = context.serial

    # what need to do in init, between [power-on, install]
    def init(self):
        time.sleep(10)
        self.serial.start_logcat()
        for i in range(2):
            self.serial.run_cmd('start adbd')
            self.serial.run_cmd('setprop persist.service.adb.enable 1')
            self.serial.run_cmd('setprop persist.service.adbd.enable 1')
            self.serial.run_cmd('setprop service.adb.root 1')
            self.serial.run_cmd('setprop persist.tcl.debug.installapk 1')
            self.serial.run_cmd('setprop persist.tcl.installapk.enable 1')
            time.sleep(2)
        self.serial.run_cmd('pm disable com.google.android.tungsten.setupwraith/.MainActivity')

        ret = self.context.adb_conn()
        if not ret:
            self.code = error.TEST_REPLY_FAIL_ADB
            self.exit()
        else:
            logging.info('adb connect success')

    # what need to do in install
    def install(self):
        context = self.context
        context.check_apk()
        context.adb.install(context.appPath, context)
        context.adb.install(context.testAppPath, context)

    # what need to do in running
    def run_instrument(self):
        context = self.context

        start = int(time.time())
        args = ['adb', '-s', context.ip, 'shell', 'am', 'instrument', '-w', '-r', '-e', 'debug', 'false',
                context.appPkgName + '.test/android.support.test.runner.AndroidJUnitRunner']
        result = ''
        child = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE)

        nbsr = NBSR(child.stdout)

        # 若进程尚未结束, popen() 返回 none
        while child.poll() is None:
            logging.debug("child.poll() is none")
            now = int(time.time())
            costTime = (now - start) / 60
            if costTime < context.timeout and costTime < 100:
                logging.debug('cost time:' + str(costTime))
                # result += child.stdout.readline()
                output = nbsr.readline(30)
                if not output:
                    logging.debug("no output")
                else:
                    result += output
            else:
                logging.debug('time out, the process will be killed')
                child.kill()
                child.wait()
                break
        logging.debug("child is over !!")
        return context.make_report(result)

    def run_monkey(self):
        context = self.context
        name = str(uuid.uuid1()) + '.result'

        output = context.adb.run_adb_cmd('adb shell monkey -p ' \
                                         + context.appPkgName \
                                         + ' --pct-trackball 20 --pct-majornav 80 --throttle 1000 -v -v -v 300 > ' + name,
                                         context)
        logging.debug(output)
        return name

    def run_with_record(self, runMethod):
        context = self.context
        context.video_record()

        result = runMethod()
        lab.context.testOver = True
        # context.videoSignal.set()
        context.pullSignal.wait()
        logging.debug('pull over')
        return result

    def uninstall(self):
        context = self.context
        logging.debug('adb uninstall')
        context.adb.uninstall(context.appPkgName, context)
        context.adb.uninstall(context.testAppPkgName, context)
        self.serial.run_cmd('rm -rf /data/data/' + context.appPkgName)
        self.serial.run_cmd('rm -rf /data/data/' + context.testAppPkgName)

    # what need to do in reset
    def reset(self):
        logging.debug('data clean')
        self.serial.run_cmd('mount -o remount rw /system')
        self.serial.run_cmd('mount -o remount rw /tvos')
        self.serial.run_cmd('mount -o remount rw /midbase')
        self.serial.run_cmd('rm -rf /data/local/tmp/*')

    # app test
    def start_app_task(self):
        context = self.context
        logging.debug('App Task')
        self.init()
        self.install()
        report = self.run_with_record(self.run_instrument)
        self.uninstall()
        self.serial.stop_logcat()
        self.serial.run_cmd('chmod 777 ' + LOGCAT)

        context.adb.run_adb_cmd("adb pull " + LOGCAT + " " + logcatfile, context)
        self.reset()
        return report

    # what need to do in info
    def get_info(self):
        info = []
        info.append('Software Version=' + self.serial.get_software_version())
        info.append('Hardware Version=' + self.serial.get_hardware_version())
        info.append('Client Type=' + self.serial.get_clientype())
        info.append('Mac=' + self.serial.get_mac())
        info.append('Ip=' + self.serial.get_ip())
        return info

    # 中间件升级
    def start_mid_task(self):

        context = self.context
        self.init()
        # 删除文件
        self.serial.run_cmd('rm -rf /data/local/tmp/')
        # 传输文件
        context.adb.run_adb_cmd('adb push ' + self.context.sitafile + '/testcase/* /data/local/tmp/', context)
        self.serial.run_cmd('mount -o remount,rw /tvos')
        # 停止中间件
        self.sita_backup()

        self.serial.run_cmd('reboot')
        # 检验开机启动是否成功
        if not self.serial.check_device_on():
            self.sita_restore()
            self.code = error.TEST_REPLY_SITA_FAIL_TO_START
            self.exit()
        # 中间件测试
        self.sita_test()
        # 还原
        self.sita_restore()
        # 数据清理
        self.reset()
        util.exit_success('')

    def sita_backup(self):
        self.serial.run_cmd('mv /tvos/bin/run.sh /tvos/bin/run.sh_bak')
        pass

    # 中间件还原
    def sita_restore(self):
        self.serial.run_cmd('mv /tvos/bin/run.sh_bak /tvos/bin/run.sh')
        pass

    def sita_test(self):
        context = self.context
        logging.debug('sita check')
        self.init()

        context.video_record()
        self.serial.run_cmd('mount -o remount,rw /tvos')
        self.serial.run_cmd('cp /data/local/tmp/testcase/tvos/bin/* /tvos/bin/')
        self.serial.run_cmd('cp /data/local/tmp/testcase/tvos/libGlibc/* /tvos/libGlibc/')

        self.serial.run_cmd('rm /data/local/tmp/sita.log')
        context.adb.run_adb_cmd("adb shell /data/local/tmp/testcase/testcase.sh > " + logcatfile, context)
        lab.context.testOver = True
        # context.videoSignal.set()
        context.pullSignal.wait()
        logging.debug('pull video over')
        # todo: pull test report
        context.adb.run_adb_cmd('adb pull /data/local/tmp/sita.log ' + logcatfile, context)

    # 整机升级
    def soft_update(self, zipfile):
        context = self.context
        if len(zipfile) <= 1:
            return
        # zipfile = '//192.168.12.104/share/V8-S828T18-LF1V017.zip'
        updatezip = zipfile.split('/')[-1]
        logging.debug(zipfile)
        logging.debug(updatezip)

        self.init()
        context.adb.run_adb_cmd('adb push ' + zipfile + ' /data/local/tmp/', context)
        self.serial.run_cmd('mv /data/local/tmp/' + updatezip + ' /data/')

        self.serial.run_cmd('mkdir -p /cache/recovery')
        self.serial.run_cmd('echo \'--update_package=/data/' + updatezip + '\n\' > /cache/recovery/command')
        self.serial.run_cmd('reboot recovery')

    # 检验结果 by uiautomator app
    def soft_check(self):
        self.serial.read_start_label()
        # waiting for 15 minutes
        for i in range(15):
            time.sleep(60)
            ipAddr = self.serial.get_ip()
            if len(ipAddr) > 1:
                return True
        self.code = error.TEST_REPLY_SOFT_FAIL_TO_START
        self.exit()

    def start_soft_task(self, updatefile):
        # context = self.context
        self.soft_update(updatefile)
        self.soft_check()
        # restore
        # self.softUpdate(argv[5], context)
        # self.softCheck()
        util.exit_success('')

    def start_monkey_task(self):
        context = self.context
        self.init()
        context.adb.install(context.appPath, context)
        context.appPkgName = util.pkg_name(context.appPath)
        # t = threading.Thread(target=self.performanceRecord, args=(context,))
        t = threading.Thread(target=self.performance_record)
        t.start()
        report = self.run_with_record(self.run_monkey)

        context.adb.uninstall(context.appPkgName, context)
        self.serial.stop_logcat()
        self.serial.run_cmd('chmod 777 ' + LOGCAT)
        time.sleep(1)
        context.adb.run_adb_cmd("adb pull " + LOGCAT + " " + logcatfile, context)
        self.reset()
        return report

    # run_adb_cmd in child thread
    def performance_record(self):
        context = self.context
        while not lab.context.testOver:
            context.adb.run_adb_cmd('adb shell dumpsys cpuinfo | grep TOTAL >> ' + cpuinfo, context)
            context.adb.run_adb_cmd('adb shell dumpsys meminfo | grep "Used RAM" >> ' + meminfo, context)
            time.sleep(context.interval)
        logging.info('performance record over')

    def exit(self):
        if self.code != error.TEST_REPLY_SUCCESS:
            if self.code == error.TEST_REPLY_FAIL_ADB:
                self.serial.run_cmd('getprop persist.service.adb.enable')
                self.serial.run_cmd('getprop persist.service.adbd.enable')
                self.serial.run_cmd('getprop service.adb.root')
                self.serial.run_cmd('getprop persist.tcl.debug.installapk')
                self.serial.run_cmd('getprop persist.tcl.installapk.enable')
            util.exit_with_error(self.code)
