import os
import re
import magic
import binwalk
import shutil
from math import log, ceil

class Extractor():
    IGNORE_DEFAULT_FMTS = ["^Non-ISO", "^ISO-8859 text"]  # default ignored file formats
    IGNORE_ALL_WILDCARD = ["ignore_all"]                  # ignore all file formats wildcard
    EXT_FILE_NAME = "{}/file_{{}}"                        # generic extracted file name
    STR_MIN_SIZE = 8                                      # min string size for taking into account when 'strings' is enabled
    NL_ENT_MIN = 3.5                                      # min entropy limit for a natural language
    NL_ENT_MAX = 5.0                                      # max entropy limit for a natural language
    ENC_ENT_MIN = 7.0                                     # min entropy limit for encrypted/compressed files
    ENC_ENT_MAX = 8.0                                     # max entropy limit for encrypted/compressed files
    STORAGE_FIELDS = 16                                   # N storage array indexes to search for

    def __init__(self, blob_exp):
        # get reference to blob explorer and copy frequently used objects
        self.logger = blob_exp.logger
        self.stats = blob_exp.stats
        self.trans_file = blob_exp.trans_file
        self.ext_dir = blob_exp.ext_dir
        self.eth_scan = blob_exp.eth_scan

        # parse extracted file name and ignored file formats
        self.ext_file_name = self.get_ext_file_path(blob_exp.ext_dir)
        self.ignored_fmt = self.get_ignored_fmts(blob_exp.args.ignored_fmt)

        # get entropy limits, strings arg and embedded flag
        self.ent_limits = self.get_entropy_limits(blob_exp.args)
        self.strings = self.get_strings_arg(blob_exp.args)
        self.embedded = self.get_embedded_arg(blob_exp.args)

        # interesting addresses that smuggled data on 'to' field in transaction
        self.tracked_addr = {}

        # already searched contracts
        self.tracked_contracts = {}


    # attempt to extract files from transactions' input data
    def extract_from_transactions(self, blk_info):
        def get_from_transaction_stub(trans, hash_id):
            # parse input data and search for files
            data = self.parse_raw_data(trans.get('input'))
            self.search_and_extract(data, "transaction", hash_id)

        # call generic transaction iter func passing stub
        self.iterate_over_transactions(get_from_transaction_stub, blk_info)

        return


    # search for files using binwalk on harvested data string coming from interesting 'from' address
    def extract_from_trans_address(self):
        self.logger.info("Starting extraction for 'to' addresses...")

        for addr,data in self.tracked_addr.items():
            try:
                # check on tracked addresses for embedded files and extract them
                files = self.get_embedded_files(data, addr)
                for file_n, file_fmt in files:
                    self.logger.info_file(f"Found file ({file_fmt}) from address '{addr}', "\
                                            f"saved to '{file_n}'...")
                    self.stats.addr_file_c += 1
            except Exception as e:
                self.logger.error(f"Unexpected error while extracting files from "\
                                    f"transaction addresses, from '{addr}': {e}")
                self.logger.error_exit()

        return


    # attempt to extract files from 'extra data' field on block information
    def extract_from_block(self, blk_info):
        # get block id
        blk_id = int(blk_info.get('number'), 16)

        try:
            # get block input data and search for files
            data = self.parse_raw_data(blk_info.get('extraData'))
            self.search_and_extract(data, "block", blk_id)
        except ValueError:
            pass
        except Exception as e:
            self.logger.error(f"Unexpected error found parsing extra data on block '{blk_id}': {e}")
            self.logger.error_exit()

        return


    # attempt to extract files from contract's storage
    def extract_from_contract(self, blk_info):
        def get_from_contract_stub(trans, hash_id):
            # get possible contract address
            contract_addr = trans.get('to', trans.get('creates'))

            if self.tracked_contracts.get(contract_addr) or not contract_addr:
                return

            # first time seeing possible contract, confirm its one and get first N data storage fields
            if self.eth_scan.get_proxy_code_at(contract_addr) != '0x':
                hex_data = ""
                for i in range(self.STORAGE_FIELDS):
                    hex_data += self.eth_scan.get_proxy_storage_position_at(
                                                address=contract_addr,
                                                position=hex(i)
                                            )

                data = self.parse_raw_data(hex_data)
                self.search_and_extract(data, "contract", hash_id)

                # mark as traversed
                self.tracked_contracts[contract_addr] = True


        # call generic transaction iter func passing stub
        self.iterate_over_transactions(get_from_contract_stub, blk_info)

        return


    # generic 'safe' iterations over transaction
    def iterate_over_transactions(self, func, blk_info):
        # iterate all over the transactions from that block
        block_trans = blk_info.get('transactions')
        for trans_obj in block_trans:
            trans_hash = trans_obj['hash']

            try:
                # here goes stub being called
                func(trans_obj, trans_hash)
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
                if not self.ignored_format(file_fmt):
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


    # main file format recognition and extraction method
    def search_and_extract(self, raw_data, ext_type, id):
        # double format string: data format, trans/block phrase, id and outfile
        gen_msg = "Found interesting file ({{}}) {} '{{}}' ({{}}), extracted to '{{}}'..."

        # format logging string
        if ext_type == "transaction":
            log_msg = gen_msg.format("inside transaction")
        elif ext_type == "block":
            log_msg = gen_msg.format("on block")
        elif ext_type == "contract":
            log_msg = gen_msg.format("on contract data at")
        else:
            raise Exception("invalid extraction type!")

        # if-elif order MATTERS here (from most accurate method to lesser one)
        # (if embedded enabled) check for embedded files inside data via binwalk
        if self.embedded and (emb_files := self.get_embedded_files(raw_data, id)):
            for file_n, file_fmt in emb_files.items():
                self.logger.info_file(log_msg.format(file_fmt, id, "found embedded", file_n))

        # (default method) check for magic bytes or file header and haven't found anything via binwalk
        elif header_f := self.get_file_via_headers(raw_data):
            file = header_f.popitem()
            self.logger.info_file(log_msg.format(file[1], id, "via file header", file[0]))

        # (if dump strings enabled) haven't found anything via binwalk nor file headers
        elif self.strings and (strings := self.dump_strings(raw_data)):
            file = strings.popitem()
            self.logger.info_file(log_msg.format(file[1], id, "via dumped strings", file[0]))

        # (if entropy search enabled) there's still the (slim) chance that utf-8 text could be hiding in that data
        elif self.ent_limits and (valid_file := self.get_file_via_entropy(raw_data)):
            file = valid_file.popitem()
            self.logger.info_file(log_msg.format(file[1], id, "via entropy calc", file[0]))

        return


    # search and extract embedded files in data via binwalk
    def get_embedded_files(self, raw_data, id):
        # create tmp file for usage with binwalk api
        tmp_n = f"tmp_{id}"
        with open(tmp_n, "+wb") as tmp_file:
            tmp_file.write(raw_data)

        files_found = {}
        ignored_file_found = False

        # search and extract files
        binwalk_res = binwalk.scan(tmp_n, signature=True, quiet=True, extract=True,
                                    dd='.*', directory=self.ext_dir)

        # traverse results
        for module in binwalk_res:
            for result in module.results:
                # check that file format is not one of ignored formats
                if self.ignored_format(result.description):
                    ignored_file_found = True
                    continue

                files_n = []
                # found valid file and extracted it
                if result.file.path in module.extractor.output:
                    ext_out = module.extractor.output[result.file.path]

                    # if file got 'carved out'
                    if carved := ext_out.carved.get(result.offset):
                        files_n.append(carved)

                    # could have also get extracted via binwalk plugins
                    if (extracted := ext_out.extracted.get(result.offset)) and extracted.files:
                        files_n.append(extracted.files[0])

                    for file in files_n:
                        # change name to our regular name convention
                        ext_file = self.ext_file_name.format(self.stats.files_c)
                        os.rename(file, ext_file)

                        self.stats.files_c += 1
                        files_found[ext_file] = result.description

        # remove tmp data file and binwalk-created dir if files get extracted
        os.remove(tmp_n)
        if files_found or ignored_file_found:
            shutil.rmtree(f"{self.ext_dir}/_{tmp_n}.extracted")

        return files_found


    # search and extract file via magic bytes or file header
    def get_file_via_headers(self, raw_data):
        found_file = {}

        # get file format with 'file' linux util
        file_fmt = magic.from_buffer(raw_data)
        # if not in ignored file format
        if not self.ignored_format(file_fmt):
            ext_file = self.ext_file_name.format(self.stats.files_c)

            # and write file into dropped files folder
            with open(ext_file, "+wb") as tmp_file:
                tmp_file.write(raw_data)

                self.stats.files_c += 1
                found_file[ext_file] = file_fmt

        return found_file


    # search and extract ascii strings into file
    def dump_strings(self, raw_data):
        found_strings = {}

        # strings were found
        if strings := self.get_strings(raw_data):
            ext_file = self.ext_file_name.format(self.stats.files_c)
            # save all into one file
            with open(ext_file, "+w") as str_file:
                for f_str in strings:
                    str_file.write(f_str + "\n")

            self.stats.files_c += 1
            found_strings[ext_file] = "ASCII Strings"

        return found_strings


    # calc entropy and extract file if entropy is between limits
    def get_file_via_entropy(self, raw_data):
        valid_files = {}
        entropy = self.stats.entropy(raw_data)

        # range in given entropy limits
        if entropy >= self.ent_limits['min'] and entropy <= self.ent_limits['max']:
            ext_file = self.ext_file_name.format(self.stats.files_c)
            # save all data into file
            with open(ext_file, "+wb") as file:
                file.write(raw_data)

            self.stats.files_c += 1
            valid_files[ext_file] = self.ent_limits['type']

        return valid_files


    # simulate the 'strings' linux util
    def get_strings(self, raw_data):
        strings = []
        final_strings = []
        curr_str = ""

        for byte in raw_data:
            # check for displayable ascii bytes
            if byte >= 0x20 and byte < 0x7F:
                curr_str += chr(byte)
            elif curr_str != "":
                    strings.append(curr_str)
                    curr_str = ""

        # return strings longer than certain length
        for ascii_str in strings:
            if len(ascii_str) >= self.STR_MIN_SIZE:
                final_strings.append(ascii_str)

        return final_strings


    # get entropy limits from args
    def get_entropy_limits(self, args):
        limits = {}
        # set for encrypted/compressed files
        if args.encrypted:
            limits['min'], limits['max'] = self.ENC_ENT_MIN, self.ENC_ENT_MAX
            limits['type'] = "Possible encrypted/compressed data"
        # set for user given limits
        elif args.custom_entropy != [-1, -1]:
            limits['min'], limits['max'] = args.custom_entropy
            limits['type'] = "From custom entropy"
        # set for unicode string search
        elif args.unicode:
            limits['min'], limits['max'] = self.NL_ENT_MIN, self.NL_ENT_MAX
            limits['type'] = "Possible UTF-8 text"

        if limits:
            self.logger.info(f"Using entropy limits of '{limits['min']}' and '{limits['max']}' for search...")

        return limits


    # check if given file format is on list
    def ignored_format(self, complete_file_fmt):
        # return instantly if ignore-all-formats wildcard was given
        if self.ignored_fmt == self.IGNORE_ALL_WILDCARD:
            return True

        for fmt in self.ignored_fmt:
            m = re.search(fmt, complete_file_fmt.lower())
            if m:
                return True

        return False


    # log if strings flag argument is enabled
    def get_strings_arg(self, args):
        if args.strings:
            self.logger.info("Search and dump ASCII strings enabled...")

        return args.strings


    # log if embedded flag argument is enabled
    def get_embedded_arg(self, args):
        if args.embedded:
            self.logger.info("Search and extract embedded files enabled...")

        return args.embedded


    # parse raw api-given data into bytes
    def parse_raw_data(self, raw_hex_data):
        hex_data = int(raw_hex_data, 16)
        data_size = ceil(log(hex_data, 2) / 8)
        data = hex_data.to_bytes(data_size, byteorder="big")

        return data


    # check ignored file format arg
    def get_ignored_fmts(self, ign_fmt):
        # ignore-all file formats wildcard enabled
        if ign_fmt == ['*']:
            return self.IGNORE_ALL_WILDCARD

        # either the default file formats or the user given ones
        elif ign_fmt == ['default_file_fmt']:
            ign_fmt = self.IGNORE_DEFAULT_FMTS

        # canonicalize file formats to lowercase (and add data "fmt")
        ign_fmt = ['^data$'] + list(map(str.lower, ign_fmt))

        return ign_fmt


    # set extracted file path
    def get_ext_file_path(self, ext_dir):
        ext_fname = self.EXT_FILE_NAME.format(ext_dir)

        return ext_fname
