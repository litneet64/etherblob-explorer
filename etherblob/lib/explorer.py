import os
import shutil
from pyfiglet import Figlet
from termcolor import colored
from time import sleep
from etherscan import Etherscan
from etherblob.lib.extractor import Extractor
from etherblob.lib.stats import Stats
from etherblob.utils.log import Logger
from etherblob.utils.wrappers import ends_gracefully


class EtherBlobExplorer():
    EXT_DIR = "ext_{}-{}"                   # extracted files dir
    TRANS_FILE = "transactions_{}-{}.txt"   # saved transactions file name
    MAX_TIME = 2**8                         # max time to retry querying again (accept 8 errors then stop increasing time)

    # make sanity checks and initialize structures
    def __init__(self, args):
        # get logger, get api key and etherscan object, create extracted files' dir
        self.args = args
        self.print_banner()
        self.logger = Logger(args)
        self.ext_dir = self.create_ext_dir(args.start_block, args.end_block, args.output_dir)
        self.api_key = self.get_apikey(args.api_key, args.api_key_path)
        self.eth_scan = Etherscan(self.api_key)

        # resolve block ids from timestamp if enabled
        args.start_block, args.end_block = self.resolve_blk_id(args.start_block,
                                                            args.end_block,
                                                            args.timestamps
                                                        )
        # copy starting block id and last retry's time power base
        self.block_id = args.start_block
        self.last_retry_t = 2

        # handler to transaction file if enabled
        self.trans_file = None

        # start stat engine and extractor passing reference to this same instance
        self.stats = Stats(self)
        self.extractor = Extractor(self)


    # main querying engine
    @ends_gracefully
    def run_engine(self):
        self.logger.info("Started EtherBlobExplorer engine...")

        # if enabled, get file for saved transactions
        if self.args.save_transactions:
            self.trans_file = open(self.TRANS_FILE, "+w")

        while (self.block_id != (self.args.end_block + 1)):
            # attempt to get this block's information
            try:
                block_info = self.get_block_info()
            except Exception as e:
                continue

            # run diff extraction modes if enabled
            if self.args.transactions:
                self.extractor.extract_from_transactions(block_info)
            if self.args.blocks:
                self.extractor.extract_from_block(block_info)
            if self.args.addresses:
                self.extractor.search_in_trans_address(block_info)
            if self.args.contracts:
                self.extractor.extract_from_contract(block_info)

            # wait to avoid triggering anti-abuse measures
            sleep(0.2)
            self.block_id += 1

            # show cycle stats
            self.stats.show_cycle_metrics()

        # close saved transactions file
        if self.args.save_transactions:
            self.trans_file.close()

        # if enabled, extract files from transactions addresses
        if self.args.addresses:
            self.extractor.extract_from_trans_address()

        # show final stats
        self.stats.show_final_metrics()

        return


    # get block information
    def get_block_info(self):
        try:
            block_info = self.eth_scan.get_proxy_block_by_number(tag = hex(self.block_id))
        except Exception as e:
            self.logger.warning(f"Problem found while querying block '{self.block_id}': {e}")
            self.logger.info(f"Sleeping for {self.last_retry_t} [s] and retrying...")
            sleep(self.last_retry_t)

            # if error happens then retry again increasing the waiting time and raise exception
            if self.last_retry_t <= self.MAX_TIME:
                self.last_retry_t = 2 * self.last_retry_t
            else:
                self.last_retry_t = self.MAX_TIME
            raise e

        return block_info


    # create dir for extracted files
    def create_ext_dir(self, s_blk, e_blk, ext_dir):
        if ext_dir == "default_ext_dir":
            ext_dir = self.EXT_DIR.format(s_blk, e_blk)

        self.logger.info(f"Creating dir for files at '{ext_dir}'...")
        try:
            os.mkdir(ext_dir)
        except Exception as e:
            self.logger.error(f"Dir '{ext_dir}' already exists...")
            self.logger.error_exit()

        return ext_dir


    # check and resolve timestamps if given
    def resolve_blk_id(self, s_blk, e_blk, parse_as_ts):
        if parse_as_ts:
            try:
                self.logger.info("Parsing blocks as timestamps...")
                s_blk = self.eth_scan.get_block_number_by_timestamp(
                                timestamp = s_blk,
                                closest = 'before'
                                )
                self.logger.info(f"Got starting block id '{s_blk}'!")

                e_blk = self.eth_scan.get_block_number_by_timestamp(
                                timestamp = e_blk,
                                closest = 'after'
                                )
                self.logger.info(f"Got ending block id '{e_blk}'!")
                s_blk, e_blk = int(s_blk), int(e_blk)
            except ValueError as e:
                self.logger.error("Error found while passing block IDs to ints!")
                self.logger.error_exit()
            except Exception as e:
                self.logger.error("Couldn't resolve timestamps to block ids!")
                self.logger.error_exit()

        return s_blk, e_blk


    # get api key from args
    def get_apikey(self, ak, ak_path):
        # api key from args is not default one
        if ak != "default_api_key":
            api_key = ak
        else:
            # attempt to get api key from file
            try:
                api_f = open(ak_path, "r")
                api_key = api_f.read().strip("\n")
                api_f.close()
            except FileNotFoundError:
                self.logger.error(f"API key not found at '{ak_path}'!")
                self.logger.error_exit()
            except Exception as e:
                self.logger.error(f"Unknown error: {e}")
                self.logger.error_exit()

        return api_key


    # print banner
    def print_banner(self):
        # get terminal's width
        term_w = shutil.get_terminal_size().columns

        # display ascii banner using pyfiglet
        f = Figlet(font = "slant", width = term_w)
        print(colored(f.renderText("<> EtherBlob Explorer"), "blue"))

        return
