import argparse

class Args():
    # get args and parse them
    @classmethod
    def get_args(cls):
        args = cls.setup_argparser()
        args = cls.parse_args(args)

        return args

    # parse args according to certain logic
    @classmethod
    def parse_args(cls, args):
        # enable transaction search mode as default only if other modes are not enabled
        if not args.blocks and not args.addresses:
            args.transactions = True

        # add 'data' to ignored file formats
        args.ignored_fmt.append("data")

        # assure ending range ID bigger than starting one
        if args.end_block < args.start_block:
            print("Invalid args: ending block ID/timetamp should be bigger than starting one!")
            exit(127)

        # assure transaction saving is only enabled if extraction from transactions mode is enabled too
        if (args.save_transactions == False) and args.transactions:
            print("Can't save transactions without transaction extracting mode!")
            exit(127)

        return args

    # setup arg parser object
    @classmethod
    def setup_argparser(cls):
        parser = argparse.ArgumentParser(description = 'Tool to search and extract blob \
                files on the Ethereum Network.',
                epilog = 'Created by litneet64. Version 1.0.0')

        # start block
        parser.add_argument('start block', type = int, help = 'Start of block id range.')
        # end block
        parser.add_argument('end block', type = int, help = 'End of block id range.')

        # enable search on transaction inputs
        parser.add_argument('--transactions', action = 'store_true', help = 'Search for \
                blob files on transaction inputs. Default search mode.')

        # enable search on block inputs
        parser.add_argument('--blocks', action = 'store_true', help = 'Search for \
                blob files on block inputs. If enabled then transaction input check is disabled \
                unless explicitly enabled.')

        # enable search on transaction addresses
        parser.add_argument('--addresses', action = 'store_true', help = 'Search for \
                blob files on \'to\' transaction addresses, as on Ethereum anyone can make \
                transactions to an arbitrary address even if it has no related owner \
                (still not very common). If enabled then transaction\'s input check \
                is disabled unless explicitly enabled.')

        # interpret start and end block ids as timestamps
        parser.add_argument('-t', '--timestamps', action = 'store_true', help = 'If enabled, then start and \
                end block IDs are interpreted as UNIX timestamps that are then resolved to the closest \
                commited blocks for that specific time.')

        # api key path
        parser.add_argument('-K', '--api-key-path', type = string, help = 'Path to file with Etherscan \
                API key for queries.', default = ".api-key")

        # api key
        parser.add_argument('-k', '--api-key', type = string, help = 'Etherscan API key as parameter. \
                If given then \'--api-key-path\' is ignored.', default = 'default_api_key')

        # extracted files' output directory
        parser.add_argument('-D', '--output-dir', type = string, help = 'Out-dir for extracted files.',
                default = "default_ext_dir")

        # output log file
        parser.add_argument('-o', '--out-log', type = string, help = 'Out-file for logs',
                default = "default_log_file")

        # save all transactions and their info
        parser.add_argument('-s', '--save-transactions', action = 'store_true', help = 'If enabled, all \
                transactions and their info are stored at file \
                \'transactions_{start-block}-{end-block}.txt\'')

        # ignored file formats
        parser.add_argument('-i', '--ignored-fmt',  help = 'Ignored file formats for extraction. \
                Default ignored/common file formats are \'ISO-8859 text\' and \'Non-ISO extended-ASCII \
                text\'. The \'data\' file format is always ignored. Accepts file format substrings and \
                makes case-insensitive matches.', nargs = '*', default = ["default_file_fmt"])

        # print version and exit
        parser.add_argument('--version', action = 'version', version = 'EtherBlob Explorer 1.0.0')

        return parser.parse_args()
