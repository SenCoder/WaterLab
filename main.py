#!/usr/bin/env python
# coding=utf-8
import sys

from lab.task import Task, BaseAgent

import time
import subprocess
import logging

from lab.task.nbstreamreader import NonBlockingStreamReader as NBSR


class TestAgent(BaseAgent):
    def sita_backup(self):
        self.serial.run_cmd('mount -o remount rw /system')
        self.serial.run_cmd('mount -o remount rw /tvos')
        self.serial.run_cmd('mount -o remount rw /midbase')
        self.serial.run_cmd('cp /tvos/bin/sitatvservice /tvos/bin/sitatvservice_bak')
        self.serial.run_cmd('cp /tvos/libGlibc/libsitatv.so /tvos/libGlibc/libsitatv.so_bak')

        self.serial.run_cmd('cp /system/lib/libsitatv.so /system/lib/libsitatv.so_bak')
        self.serial.run_cmd('cp /system/lib/libcom_tcl_tv_jni.so /system/lib/libcom_tcl_tv_jni.so_bak')
        self.serial.run_cmd('cp /system/framework/com.tcl.tvmanager.jar /system/framework/com.tcl.tvmanager.jar_bak')

    def sita_replace(self):
        self.serial.run_cmd('cp debug/bin/* /tvos/bin/ -f')
        self.serial.run_cmd('cp debug/lib/* /system/lib/ -f')

    def sita_restore(self):
        self.serial.run_cmd('mount -o remount rw /system')
        self.serial.run_cmd('mount -o remount rw /tvos')
        self.serial.run_cmd('mount -o remount rw /midbase')
        self.serial.run_cmd('cp /tvos/bin/sitatvservice_bak /tvos/bin/sitatvservice')
        self.serial.run_cmd('cp /tvos/libGlibc/libsitatv.so_bak /tvos/libGlibc/libsitatv.so')

        self.serial.run_cmd('cp /system/lib/libsitatv.so_bak /system/lib/libsitatv.so')
        self.serial.run_cmd('cp /system/lib/libcom_tcl_tv_jni.so_bak /system/lib/libcom_tcl_tv_jni.so')
        self.serial.run_cmd('cp /system/framework/com.tcl.tvmanager.jar_bak /system/framework/com.tcl.tvmanager.jar')

    def run_instrument(self):
        context = self.context

        start = int(time.time())
        args = ['adb', '-s', context.ip, 'shell', 'am', 'instrument', '-w', '-r', '-e', 'debug', 'false',
                context.appPkgName + '.test/android.support.test.runner.AndroidJUnitRunner']
        result = ''
        child = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE)

        nbsr = NBSR(child.stdout)
        no_output_count = 0

        while child.poll() is None:
            logging.debug("child.poll() is none")
            now = int(time.time())
            costTime = (now - start) / 60
            if costTime < context.timeout and costTime < 100 and no_output_count < 20:
                logging.debug('cost time:' + str(costTime))
                # result += child.stdout.readline()
                output = nbsr.readline(30)
                if not output:
                    no_output_count += 1
                    logging.debug("no output " + str(no_output_count))
                else:
                    no_output_count = 0
                    result += output
            else:
                logging.debug('time out, the process will be killed')
                child.kill()
                child.wait()
                break
        logging.debug("child is over !!")
        return context.make_report(result)


if __name__ == '__main__':
    agent = TestAgent()
    with Task(agent) as task:
        task.start(sys.argv)
