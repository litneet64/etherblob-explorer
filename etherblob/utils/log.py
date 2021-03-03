import logging
import sys
from termcolor import colored

class Logger():
    FILE_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
    STDOUT_FORMAT = colored("%(asctime)s ", "yellow") + "%(message)s"
    OUT_LOG = "etherblob_{}-{}.log"
    INFO = "{} ".format(colored("[INFO]", "blue"))
    WARNING = "{} ".format(colored("[WARN]", "red"))
    ERROR = "{} ".format(colored("[ERROR]", "white", "on_red", ['blink']))
    INFO_FILE = "{} ".format(colored("[INFO]", "blue", "on_cyan", ['bold']))


    def __init__(self, args):
        self.out_log = self.get_outlog(args.start_block, args.end_block, args.out_log)
        self.cons_logger, self.file_logger = self.logging_setup()


    # setup logging config for stdout and a file
    def logging_setup(self):
        # set formatter and create 2 loggers
        stdout_fmt = logging.Formatter(self.STDOUT_FORMAT)
        file_fmt = logging.Formatter(self.FILE_FORMAT)
        file_log = logging.getLogger("file_handler")
        cons_log = logging.getLogger("cons_handler")

        # create file handler and attach to file logger
        file_hdlr = logging.FileHandler(self.out_log)
        file_hdlr.setFormatter(file_fmt)
        file_hdlr.setLevel(logging.INFO)
        file_log.addHandler(file_hdlr)

        # create console handler and attach to console logger
        cons_hdlr = logging.StreamHandler(sys.stdout)
        cons_hdlr.setFormatter(stdout_fmt)
        cons_hdlr.setLevel(logging.INFO)
        cons_log.addHandler(cons_hdlr)

        # set logger levels
        cons_log.setLevel(logging.INFO)
        file_log.setLevel(logging.INFO)

        return cons_log, file_log


    # get log-file name
    def get_outlog(self, s_blk, e_blk, out_log):
        if out_log == "default_log_file":
            out_log = self.OUT_LOG.format(s_blk, e_blk)

        return out_log


    # wrapper around exit with logging message
    def error_exit(self):
        self.error("Exiting...")
        exit(127)

    # wrapper around 'logging' info for Logger class
    def info(self, msg):
        self.file_logger.info(msg)
        self.cons_logger.info(self.INFO + msg)

        return

    # wrapper around 'logging' info when files are found
    def info_file(self, msg):
        self.file_logger.info(msg)
        self.cons_logger.info(self.INFO_FILE + msg)

        return

    # wrapper around 'logging' warning for Logger class
    def warning(self, msg):
        self.file_logger.warning(msg)
        self.cons_logger.warning(self.WARNING + msg)

        return

    # wrapper around 'logging' error for Logger class
    def error(self, msg):
        self.file_logger.error(msg)
        self.cons_logger.error(self.ERROR + msg)

        return
