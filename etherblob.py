#!/usr/bin/python3

import etherblob
from etherblob.lib.explorer import EtherBlobExplorer
from etherblob.utils.args import Args


if __name__ == "__main__":
    # get args
    args = Args.get_args()

    # instantiate main explorer
    explorer = EtherBlobExplorer(args)
    explorer.run_engine()
