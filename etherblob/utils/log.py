import logging
import sys

class Logger():
    FORMAT = "%(asctime)s [%(levelname)s] %(message)s"

    # setup logging config for stdout and a file
    @classmethod
    def logging_setup(cls, s_block, e_block, out_log):
        # set formatter and get root logger
        log_fmt = logging.Formatter(cls.FORMAT)
        root_log = logging.getLogger()

        # create file handler and attach to root logger
        file_hdlr = logging.FileHandler(out_log.format(s_block, e_block))
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
    @staticmethod
    def error_exit():
        logging.error("Exiting...")
        exit(127)
