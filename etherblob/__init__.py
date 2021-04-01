
__version__ = '2.1.0'

def main():
    from etherblob.lib.explorer import EtherBlobExplorer
    from etherblob.utils.args import Args

    # get args
    args = Args.get_args()

    # instantiate main explorer
    explorer = EtherBlobExplorer(args)
    explorer.run_engine()


if __name__ == "__main__":
    main()
