from time import time

class Stats():
    WAIT_TIME = 60      # time to wait until showing metrics

    def __init__(blob_exp):
        self.logger = blob_exp.logger
        self.blob_explorer = blob_exp
        self.total_blocks = 
        self.last_time = -1

    # get overall progress metrics since a certain time
    def get_metrics(self):
        if (time() - self.last_time) >= self.WAIT_TIME:
            self.logger.info(f"Parsed {block_id - s_block}/{self.total_blocks} \
                            blocks and {trans_c} transactions...")
            last_t = time()

        return last_time
