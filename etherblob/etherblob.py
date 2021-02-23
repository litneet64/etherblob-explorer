#!/usr/bin/python3

import etherblob
from etherblob.lib.explorer import EtherBlobExplorer
from etherblob.utils.arg import Args
from etherblob.utils.log import Logger


if __name__ == "__main__":
    # get args
    args = Args.get_args()

    # setup logging config
    logging = Logger.logging_setup(args.start_block, args.end_block, args.out_log)

    # block id iterator and total of blocks
    block_id = s_block
    total_blocks = e_block - s_block

    # dropped file and transaction counter
    file_c = 0
    trans_c = 0

    # create out file with all transactions found
    with open(f"transactions_{s_block}-{e_block}.txt", "+w") as trans_file:
        # define first last time and last retry time
        last_t = time()
        last_retry_t = 2

        # iterate over all the required blocks
        while (block_id != (e_block + 1)):
            # measure current time
            curr_t = time()

            try:
                block_info = eth.get_proxy_block_by_number(tag = hex(block_id))
            except Exception as e:
                logging.warning(f"Problem found while querying block '{block_id}': {e}")
                logging.info(f"Sleeping for {last_retry_t} [s] and retrying...")
                sleep(last_retry_t)
                last_retry_t = last_retry_t * 2 if last_retry_t <= MAX_TIME else MAX_TIME
                continue

            block_trans = block_info.get('transactions')

            # iterate all over the transactions from that block
            for trans_obj in block_trans:
                trans_hash = trans_obj['hash']
                trans_data = trans_obj['input']

                try:
                    # transform input string into bytes, if we even have input
                    hex_data = int(trans_data, 16)
                    data_size = ceil(log(hex_data, 2) / 8)
                    data = hex_data.to_bytes(data_size, byteorder="big")

                    # check for magic bytes or file header
                    file_fmt = magic.from_buffer(data)
                    for fmt in IGNORED_FMTS:
                        # if file format not in ignore list
                        if fmt not in file_fmt:
                            dropped_file = FILE_NAME.format(file_c)
                            logging.info(f"Found interesting file ({file_fmt}) in transaction '{trans_hash}', dropped to '{dropped_file}'...")

                            # and write file into dropped files folder
                            with open(dropped_file, "+wb") as drop_file:
                                drop_file.write(data)

                            file_c += 1

                except ValueError as e:
                    # otherwise skip to next transaction after saving it to file
                    pass
                except Exception as e:
                    # error not caught, inform
                    logging.error(f"Error found parsing input data on trans '{trans_hash}': {e}")
                finally:
                    # and save them into transaction file anyway
                    trans_file.write(f"[*] Transaction {trans_hash}\n")
                    for k,v in trans_obj.items():
                        if k != 'hash':
                            trans_file.write(f"\t[-] {k}: {v}\n")
                    trans_file.write("\n")

                    # increment transaction counter anyway
                    trans_c += 1

            # wait to avoid triggering anti-abuse measures
            sleep(0.2)
            block_id += 1

            # show progress after 60s
            if (curr_t - last_t) >= 60:
                logging.info(f"Parsed {block_id - s_block}/{total_blocks} blocks and {trans_c} transactions...")
                last_t = time()

    logging.info(f"Finished downloading/reviewing all {total_blocks} blocks!")
    logging.info(f"Total number of transactions {trans_c}!")
