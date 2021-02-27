import os
import traceback

# if error occurs on engine when there's no progress so far, then remove log and dir
def ends_gracefully(func):
    def wrap(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            self = args[0]
            # file size is 0
            if os.path.getsize(self.logger.out_log):
                os.remove(self.logger.out_log)
            # dir is empty
            if not os.listdir(self.ext_dir):
                os.rmdir(self.ext_dir)

            # inform about error
            self.logger.error(f"Unhandled error on engine: {e}")
            traceback.print_exc()
            self.logger.error_exit()

        return

    return wrap
