import os
import re
import magic
import binwalk
from math import log, ceil

class Extractor():
    IGNORED_FMTS = ["data", "Non-ISO", "ISO-8859 text"]     # default ignored file formats
    EXT_FILE_NAME = "{}/file_{{}}"                          # generic extracted file name

    def __init__(self, blob_exp):
        # get reference to blob explorer and copy frequently used objects
        self.logger = blob_exp.logger
        self.stats = blob_exp.stats
        self.trans_file = blob_exp.trans_file

        # parse extracted file name and ignored file formats
        self.ext_file_name = self.get_ext_file_path(blob_exp.ext_dir)
        self.ignored_fmt = self.get_ignored_fmts(blob_exp.args.ignored_fmt)

        # interesting addresses that smuggled data on 'to' field in transaction
        self.tracked_addr = {}


    # generic file format recognition
    def get_file_format_and_extract(self, raw_data, ext_type, id):
        # double format string: data format, trans/block phrase, id and outfile
        gen_msg = "Found interesting file ({{}}) {} '{{}}', extracted to '{{}}'..."

        # format logging string
        if ext_type == "transaction":
            log_msg = gen_msg.format("inside transaction")
        elif ext_type == "block":
            log_msg = gen_msg.format("on block")
        else:
            raise Exception("invalid extraction type!")

        # check for magic bytes or file header
        file_fmt = magic.from_buffer(raw_data)
        if self.not_ignored_format(file_fmt):
            ext_file = self.ext_file_name.format(self.stats.files_c)
            self.logger.info(log_msg.format(file_fmt, id, ext_file))

            # and write file into dropped files folder
            with open(ext_file, "+wb") as tmp_file:
                tmp_file.write(raw_data)

            self.stats.files_c += 1

        return


    # attempt to extract files from transactions' input data
    def extract_from_transactions(self, blk_info):
        # iterate all over the transactions from that block
        block_trans = blk_info.get('transactions')
        for trans_obj in block_trans:
            trans_hash = trans_obj['hash']

            try:
                # parse input data and search for files
                data = self.parse_raw_data(trans_obj.get('input'))
                self.get_file_format_and_extract(data, "transaction", trans_hash)

            except ValueError as e:
                # skip when no input data is found
                pass
            except Exception as e:
                self.logger.error(f"Unexpected error found parsing input data on trans '{trans_hash}': {e}")
                self.logger.error_exit()
            finally:
                if self.trans_file:
                    # save details into transaction file
                    self.trans_file.write(f"[*] Transaction {trans_hash}\n")
                    for k,v in trans_obj.items():
                        if k != 'hash':
                            self.trans_file.write(f"\t[-] {k}: {v}\n")
                    self.trans_file.write("\n")

                self.stats.trans_c += 1

        return


    # attempt to find files along recievers addresses
    def search_in_trans_address(self, blk_info):
        block_trans = blk_info.get('transactions')
        for trans_obj in block_trans:
            trans_hash = trans_obj['hash']
            from_addr = trans_obj['from']

            try:
                # 'to' address is empty when creating a contract (uses field 'creates')
                if not trans_obj['to']:
                    continue

                # parse 'to' addresses into bytes and search for file header or magic bytes
                data = self.parse_raw_data(trans_obj['to'])
                file_fmt = magic.from_buffer(data)

                # if we got file header or magic bytes at head of file...
                if self.not_ignored_format(file_fmt):
                    # and it's first time finding this 'from' address
                    if not self.tracked_addr.get(from_addr):
                        self.tracked_addr[from_addr] = b""
                        self.logger.info(f"Found file header in transaction '{trans_hash}' "\
                                            f"coming from address '{from_addr}'...")

                # check if it's coming from already tracked address and append data
                if self.tracked_addr.get(from_addr):
                    self.tracked_addr[from_addr] += data
                    self.logger.info(f"Adding more data to possible file from address '{from_addr}'...")

            except Exception as e:
                self.logger.error(f"Unexpected error found parsing 'to' address data on trans '{trans_hash}': {e}")
                self.logger.error_exit()

        return


    # attempt to extract files from 'extra data' field on block information
    def extract_from_block(self, blk_info):
        # get block id
        blk_id = int(blk_info.get('number'), 16)

        try:
            # get block input data and search for files
            data = self.parse_raw_data(blk_info.get('extraData'))
            self.get_file_format_and_extract(data, "block", blk_id)
        except ValueError:
            pass
        except Exception as e:
            self.logger.error(f"Unexpected error found parsing extra data on block '{blk_id}': {e}")
            self.logger.error_exit()

        return


    # search for files using binwalk on harvested data string coming from interesting 'from' address
    def extract_from_trans_address(self):
        self.logger.info("Starting extraction for 'to' addresses...")

        for addr,data in self.tracked_addr.items():
            # create tmp file for usage with binwalk and write data into it
            tmp_n = f"tmp_{addr}"
            with open(tmp_n, "+wb") as tmp_file:
                tmp_file.write(data)

            try:
                # check inside data file for embedded files and extract them
                for module in binwalk.scan(tmp_n, signature=True, quiet=True, extract=True):
                    for result in module.results:
                        # found valid file and got extracted
                        if result.file.path in module.extractor.output:
                            file_n =  module.extractor.output[result.file.path].extracted[result.offset].files[0]
                            self.logger.info(f"Found file ({result.description}) from address '{addr}', "\
                                                f"saved to '{file_n}'...")
                            self.stats.files_c += 1
                            self.stats.addr_file_c += 1
                # remove tmp data file
                os.remove(tmp_n)
            except Exception as e:
                self.logger.error(f"Unexpected error while extracting files from "\
                                    f"transaction addresses, from '{addr}': {e}")
                self.logger.error_exit()

        return


    # check if given file format is on list
    def not_ignored_format(self, complete_file_fmt):
        for fmt in self.ignored_fmt:
            m = re.search(fmt, complete_file_fmt.lower())
            if m:
                return False

        return True


    # parse raw api-given data into bytes
    def parse_raw_data(self, raw_hex_data):
        hex_data = int(raw_hex_data, 16)
        data_size = ceil(log(hex_data, 2) / 8)
        data = hex_data.to_bytes(data_size, byteorder="big")

        return data


    # check ignored file format arg
    def get_ignored_fmts(self, ign_fmt):
        # either the default file formats or the user given ones
        if 'default_file_fmt' in ign_fmt:
            ign_fmt = self.IGNORED_FMTS

        # canonicalize file formats to lowercase
        ign_fmt = list(map(str.lower, ign_fmt))

        return ign_fmt


    # set extracted file path
    def get_ext_file_path(self, ext_dir):
        ext_fname = self.EXT_FILE_NAME.format(ext_dir)

        return ext_fname
