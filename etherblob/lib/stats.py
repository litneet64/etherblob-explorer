from time import time

class Stats():
    WAIT_TIME = 60      # time to wait until showing metrics

    def __init__(blob_exp):
        self.logger = blob_exp.logger
        self.blob_explorer = blob_exp
        self.total_blocks = blob_exp.args.end_block - blob_exp.args.start_block
        self.last_time = time()

    # show overall progress metrics since a certain time
    def show_cycle_metrics(self):
        if (time() - self.last_time) >= self.WAIT_TIME:
            self.logger.info(f"Parsed {block_id - s_block}/{self.total_blocks} \
                            blocks and {trans_c} transactions...")
            self.last_time = time()

        return

    # show final metrics
    def show_final_metrics(self):
        logging.info(f"Finished downloading/reviewing all {total_blocks} blocks!")
        logging.info(f"Total number of transactions {trans_c}!")

        return
