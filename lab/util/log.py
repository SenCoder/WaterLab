import logging
import os

from datetime import datetime


def setlog(flag):
    today = datetime.now()
    logpath = 'log/'
    if not os.path.exists(logpath):
        os.makedirs(logpath)
    fmt = '%(asctime)s %(filename)s %(funcName)s %(lineno)s %(levelname)s %(message)s'

    logging.basicConfig(format=fmt,
                        level=logging.DEBUG,
                        filename=logpath + str(today.year) + '-' + str(today.month) + '-' + str(
                            today.day) + '-' + flag + '.log',
                        filemode='a')
