import logging
import sys

class Logger():
    FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
    OUT_LOG = "etherblob_{}-{}.log"


    def __init__(self, args):
        self.logger = self.logging_setup(args.start_block, args.end_block, args.out_log)


    # setup logging config for stdout and a file
    @classmethod
    def logging_setup(cls, s_block, e_block, out_log):
        if out_log == "default_log_file":
            out_log = cls.OUT_LOG.format(s_block, e_block)

        # set formatter and get root logger
        log_fmt = logging.Formatter(cls.FORMAT)
        root_log = logging.getLogger()

        # create file handler and attach to root logger
        file_hdlr = logging.FileHandler(out_log)
        file_hdlr.setFormatter(log_fmt)
        file_hdlr.setLevel(logging.INFO)
        root_log.addHandler(file_hdlr)

        # create console handler and attach to root logger
        cons_hdlr = logging.StreamHandler(sys.stdout)
        cons_hdlr.setFormatter(log_fmt)
        cons_hdlr.setLevel(logging.INFO)
        root_log.addHandler(cons_hdlr)

        root_log.setLevel(logging.INFO)

        return root_log


    # wrapper around exit with logging message
    def error_exit(self):
        self.error("Exiting...")
        exit(127)

    # wrapper around 'logging' info for Logger class
    def info(self, msg):
        self.logger.info(msg)

        return

    # wrapper around 'logging' warning for Logger class
    def warning(self, msg):
        self.logger.warning(msg)

        return

    # wrapper around 'logging' error for Logger class
    def error(self, msg):
        self.logger.error(msg)

        return
