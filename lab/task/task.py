import logging

import lab.util.log as log
from lab.const import error
from lab.context import RunContext
from lab.util import util
import lab


class Task(object):
    def __init__(self, agent):
        self.agent = agent

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.info("===Task Exit===")
        self.agent.exit()

    def start(self, args):
        util.check_param(args)
        log.setlog(args[2])

        logging.debug("Task Start")
        ctx = RunContext(args[2], args[3])

        self.agent.set_context(ctx)
        if args[1] in lab.options[0:5]:
            ctx.set_app_path(args[4], args[5])
            ctx.set_pkg_name()
            if args[1] == 'init':
                self.agent.init()
            elif args[1] == 'install':
                self.agent.install()
            elif args[1] == 'run':
                report = self.agent.run_with_record(self.agent.run_instrument)
                util.exit_success(report)
            elif args[1] == 'reset':
                self.agent.uninstall()
                self.agent.reset()
            elif args[1] == 'app':
                ctx.set_timeout(args[6])
                report = self.agent.start_app_task()
                util.exit_success(report)
        elif args[1] == 'monkey':
            ctx.set_app_path(args[4], '')
            ctx.interval = int(args[5])
            report = self.agent.start_monkey_task()
            util.exit_success(report)
        elif args[1] == 'info':
            info = self.agent.get_info()
            util.exit_info(info)
        elif args[1] == 'mid':
            ctx.set_sita_path(args[4])
            self.agent.start_mid_task()
        elif args[1] == 'system':
            self.agent.start_soft_task()
        else:
            self.agent.code = error.TEST_REPLY_FAIL_WRONG_CMD
