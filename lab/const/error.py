# error code
TEST_REPLY_SUCCESS = 100
TEST_REPLY_FAIL_NODEVICE = 101
TEST_REPLY_FAIL_RPC = 102
TEST_REPLY_FAIL_POWER = 103
TEST_REPLY_FAIL_SERIAL = 104
TEST_REPLY_FAIL_ADB = 105
TEST_REPLY_FAIL_INSTALL = 106
TEST_REPLY_FAIL_RUN = 107
TEST_REPLY_FAIL_UNKNOWN = 108
TEST_REPLY_FAIL_TIMEOUT = 109
TEST_REPLY_FAIL_WRONG_CMD = 110
TEST_REPLY_SITA_FAIL_TO_START = 111
TEST_REPLY_SOFT_FAIL_TO_START = 112

# error description
TEST_SUCCESS = "Test Finish"
TEST_FAIL_NODEVICE = "No Device Error"
TEST_FAIL_RPC = "RPC Error"
TEST_FAIL_POWER = "Power Error"
TEST_FAIL_SERIAL = "Serial Error"
TEST_FAIL_ADB = "Adb Error"
TEST_FAIL_INSTALL = "Install Error"
TEST_FAIL_RUN = "Running Error"
TEST_FAIL_UNKNOWN = "Unknown Error"
TEST_FAIL_TIMEOUT = "Timeout Error"
TEST_FAIL_WRONG_CMD = "Params Error"
TEST_SITA_FAIL_TO_START = "Fail to Start After Sita Update"
TEST_SOFT_FAIL_TO_START = "Fail to Start After Software Update"


def get_desc_by_code(code):
    if code == TEST_REPLY_SUCCESS:
        return TEST_SUCCESS
    elif code == TEST_REPLY_FAIL_NODEVICE:
        return TEST_FAIL_NODEVICE
    elif code == TEST_REPLY_FAIL_RPC:
        return TEST_FAIL_RPC
    elif code == TEST_REPLY_FAIL_POWER:
        return TEST_FAIL_POWER
    elif code == TEST_REPLY_FAIL_SERIAL:
        return TEST_FAIL_SERIAL
    elif code == TEST_REPLY_FAIL_ADB:
        return TEST_FAIL_ADB
    elif code == TEST_REPLY_FAIL_INSTALL:
        return TEST_FAIL_INSTALL
    elif code == TEST_REPLY_FAIL_RUN:
        return TEST_FAIL_RUN
    elif code == TEST_REPLY_FAIL_UNKNOWN:
        return TEST_FAIL_UNKNOWN
    elif code == TEST_REPLY_FAIL_TIMEOUT:
        return TEST_FAIL_TIMEOUT
    elif code == TEST_REPLY_FAIL_WRONG_CMD:
        return TEST_FAIL_WRONG_CMD
    elif code == TEST_REPLY_SITA_FAIL_TO_START:
        return TEST_SITA_FAIL_TO_START
    elif code == TEST_SITA_FAIL_TO_START:
        return TEST_SOFT_FAIL_TO_START
    return TEST_FAIL_UNKNOWN
