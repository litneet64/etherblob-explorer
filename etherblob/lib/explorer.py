import os
from time import sleep
from etherscan import Etherscan
from etherblob.lib.extractor import Extractor
from etherblob.lib.stats import Stats

class EtherBlobExplorer():
    EXT_DIR = "ext_{}-{}"                   # extracted files dir
    EXT_FILE_NAME = "{}/file_{{}}"          # generic extracted file name
    TRANS_FILE = "transactions_{}-{}.txt"   # saved transactions file name
    MAX_TIME = 2**8                         # max time to retry querying again (accept 8 errors then stop increasing time)

    # make sanity checks and initialize structures
    def __init__(self, logger, args):
        # get logger, get api key and etherscan object
        self.args = args
        self.logger = logger
        self.api_key = self.get_apikey(args.api_key, args.api_key_path)
        self.eth_scan = Etherscan(self.api_key)

        # resolve block ids from timestamp if enabled
        args.start_block, args.end_block = self.resolve_blk_id(args.start_block,
                                                            args.end_block,
                                                            args.timestamps
                                                        )
        # copy starting block id and set last retry's time power base
        self.block_id = args.start_block
        self.last_retry_t = 2

        # start stat engine and extractor
        self.extractor = Extractor()
        self.stats = Stats()


    # main querying engine
    def run_engine(self):
        # extracted file and transaction counters
        file_c = 0
        trans_c = 0

        # if enabled, get file for saved transactions
        if self.args.save_transactions:
            trans_file = open(self.TRANSFILE, "+w")

        while (self.block_id != (self.args.end_block + 1)):
            # attempt to get this block's information
            try:
                block_info = self.get_block_info()
            except Exception as e:
                continue

            if self.args.transactions:
                pass
            if self.args.blocks:
                pass
            if self.args.addresses:
                pass

            # wait to avoid triggering anti-abuse measures
            sleep(0.2)
            block_id += 1

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
    def create_ext_dir(self, s_blk, e_blk):
        ext_dir = EXT_DIR.format(s_blk, e_blk)
        self.logger.info(f"Creating dir for files at '{ext_dir}'...")
        try:
            os.mkdir(ext_dir)
        except Exception as e:
            self.logger.error(f"Dir '{ext_dir}' already exists...")
            self.logger.error_exit()

        return


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
            except Exception as e:
                self.logger.error("Couldn't resolve timestamps to block ids!")
                self.logger.error_exit()

        return s_blk, e_blk


    # get api key from args
    def get_apikey(self, ak, ak_path):
        # api key from args not empty
        if ak:
            api_key = ak
        else:
            # attempt to get api key from file
            try:
                api_f = open(ak_path, "r")
                api_key = api_f.read().strip("\n")
                api_f.close()
            except Exception as e:
                self.logger.error(f"Error: api key not found on '{ak_path}'!")
                self.logger.error_exit()

        return api_key
