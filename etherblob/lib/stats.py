from time import time

class Stats():
    WAIT_TIME = 60      # time to wait until showing metrics

    def __init__(self, blob_exp):
        self.logger = blob_exp.logger
        self.blob_exp = blob_exp
        self.total_blocks = blob_exp.args.end_block - blob_exp.args.start_block

        # last time and block recorded on previous cycle
        self.last_time = time()
        self.last_blk_n = 0

        # counters for interesting stats
        self.files_c = 0
        self.trans_c = 0
        self.addr_file_c = 0

        # message to show every 60s
        self.cycle_msg = f"Parsed {{}}/{self.total_blocks} blocks ({{}} [block]/[min]), "
        self.cycle_msg += "found {} files so far"


    # show overall progress metrics since a certain time
    def show_cycle_metrics(self):
        if (time() - self.last_time) >= self.WAIT_TIME:
            # format template message with dynamic block data
            curr_blk = self.blob_exp.block_id - self.blob_exp.args.start_block
            msg = self.cycle_msg.format(curr_blk, curr_blk - self.last_blk_n,
                                        self.files_c)

            # append data to cycle message with correct args according to extraction mode
            if self.blob_exp.args.transactions:
                msg += f" and {self.trans_c} transactions"
            if self.blob_exp.args.addresses:
                msg += f" {self.trans_c} transactions, and "\
                        f"{len(self.blob_exp.extractor.tracked_addr)} interesting addresses"
            msg += "..."

            self.logger.info(msg)

            # record new milestones
            self.last_time = time()
            self.last_blk_n = curr_blk

        return

    # show final metrics
    def show_final_metrics(self):
        self.logger.info(f"Finished exploring all {self.total_blocks} blocks!")
        self.logger.info(f"Total of extracted files: {self.files_c}")

        # show extra info if these extraction modes were enabled
        if self.blob_exp.args.transactions or self.blob_exp.args.addresses:
            self.logger.info(f"Total of transactions: {self.trans_c}")
        if self.blob_exp.args.addresses:
            self.logger.info(f"Total of interesting addresses: "\
                            f"{len(self.blob_exp.extractor.tracked_addr)}")
            self.logger.info(f"Total of files found on interesting addresses: {self.addr_file_c}")

        return
