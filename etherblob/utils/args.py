import argparse
import etherblob

class Args():
    # get args and parse them
    @classmethod
    def get_args(cls):
        args = cls.setup_argparser()
        args = cls.validate_args(args)

        return args


    # print message and exit
    @staticmethod
    def print_exit(msg):
        print(msg)
        exit(127)

        return


    # validate args according to certain logic (on error, should make program end on the spot)
    @classmethod
    def validate_args(cls, args):
        # enable transaction search mode as default only if other modes are not enabled
        if not args.blocks and not args.addresses and not args.contracts:
            args.transactions = True

        # enable file header search as default only if other locations are not enabled
        if not args.embedded and not args.unicode and not args.encrypted \
        and not args.strings and args.custom_entropy == [-1, -1]:
            args.file_header = True

        # assure ending range ID bigger than starting one
        if args.end_block < args.start_block:
            cls.print_exit("Invalid args: ending block ID/timetamp should be bigger than starting one!")

        # assure transaction saving is only enabled if extraction from transactions mode is enabled too
        if (args.transactions == False) and args.save_transactions:
            cls.print_exit("Can't save transactions without transaction extracting mode!")

        # assure entropy custom limits are between 0 and 8, and they make sense
        if (ent := args.custom_entropy) != [-1, -1]:
            valid = True
            if ent[0] > ent[1]:
                valid = False
            elif ent[0] < 0 or ent[0] > 8:
                valid = False
            elif ent[1] < 0 or ent[1] > 8:
                valid = False

            if not valid:
                cls.print_exit("Entropy limits should be between 0.0 and 8.0 and with first < second!")

        # assure custom entropy limits and encrypted/unicode flag are not set at same time
        if ((args.encrypted or args.unicode) and args.custom_entropy != [-1, -1]) \
        or (args.encrypted and args.unicode):
            cls.print_exit("Custom entropies/encrypted/unicode flag should be used separately!")

        # assure sane storage array indexes and check that it's only selected when '--contracts' is enabled
        if (cont_pos := args.contract_position) != -1:
            if not args.contracts:
                cls.print_exit("Invalid args: '--contract-position' should be enabled only when "\
                            "'--contracts' is enabled too!")
            elif cont_pos <= 0:
                cls.print_exit("Contract position should be positive!")

        return args


    # setup arg parser object
    @classmethod
    def setup_argparser(cls):
        parser = argparse.ArgumentParser(description = 'Tool to search and extract blob \
                files on the Ethereum Network.',
                epilog = 'Official GitHub repo \'https://github.com/litneet64/etherblob-explorer\'')

        # start block
        parser.add_argument('start_block', type = int, help = 'Start of block id range.')
        # end block
        parser.add_argument('end_block', type = int, help = 'End of block id range.')

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

        # enable serach on contract's storage
        parser.add_argument('--contracts', action = 'store_true', help = 'Search for \
                blob files on contract\'s storage. If enabled then transaction input \
                check is disabled unless explicitly enabled.')

        # choose blockchain net
        parser.add_argument('--network', '-N', type = str.lower, help = 'Choose blockchain \
                network to search in. Available choices are Main, Goerli (Görli), Kovan, \
                Rinkeby and Ropsten. MainNet is the default network. Case-insensitive.',
                choices = ['main', 'goerli', 'kovan', 'rinkeby', 'ropsten'],
                default = 'main')

        # enable file header search
        parser.add_argument('-H', '--file-header', action = 'store_true', help = 'If enabled,\
                search for file formats via magic bytes/file headers on data \
                (from blocks, transactions or addresses). \
                Enabled by default unless another method is enabled too.')

        # enable embedded file search
        parser.add_argument('-M', '--embedded', action = 'store_true', help = 'If enabled,\
                search for embedded files on data (from blocks, transactions or addresses) via \
                binwalk. Disabled by default as parsing now takes longer.')

        # search via entropy
        parser.add_argument('-U', '--unicode', action = 'store_true', help = 'If enabled, \
                attempt to search and dump files containing UTF-8 text from \
                harvested data (blocks, transactions, addresses) using \
                Shannon\'s Entropy (between 3.5 and 5.0) if no other discernible file is \
                found first on that data. Yields many false positives.')

        # get user's custom entropy limits
        parser.add_argument('-E', '--custom-entropy', type = float, help = 'Define your own entropy \
                limits (min and max) to search for files/data on harvested data.', nargs = 2, \
                default = [-1.0, -1.0])

        # get encrypted data
        parser.add_argument('--encrypted', action = 'store_true', help = 'If enabled, attempt \
                to search and dump encrypted/compressed data found via different search methods \
                (blocks, transactions, addresses) using Shannon\'s Entropy (between 7.0 and 8.0) \
                if no other discernible file is found first on that data.')

        # search for strings
        parser.add_argument('-S', '--strings', action = 'store_true', help = 'If enabled, attempt to \
                search and dump ASCII strings into files found inside harvested data \
                (blocks, transactions, addresses) if no other discernible file is \
                found first on that data.')

        # search until the (N-1)th position at contract's storage array
        parser.add_argument('-C', '--contract-position', type = int, help = 'Search inside contract\'s data \
                until reaching the (N-1)th position on its storage array. Positions contain 32 \
                bytes worth of data. Count starts at 0 and default pos is the 15th pos \
                (16 indexes in total) if no custom position is given.', default = -1)

        # interpret start and end block ids as timestamps
        parser.add_argument('-t', '--timestamps', action = 'store_true', help = 'If enabled, then start and \
                end block IDs are interpreted as UNIX timestamps that are then resolved to the closest \
                commited blocks for those specific times.')

        # api key path
        parser.add_argument('-K', '--api-key-path', type = str, help = 'Path to file with Etherscan \
                API key for queries. Default search location is \'.api-key\'.', default = ".api-key")

        # api key
        parser.add_argument('-k', '--api-key', type = str, help = 'Etherscan API key as parameter. \
                If given then \'--api-key-path\' is ignored.', default = 'default_api_key')

        # extracted files' output directory
        parser.add_argument('-D', '--output-dir', type = str, help = 'Out-dir for extracted files. \
                Default is \'ext_{start block}-{end block}\'.', default = "default_ext_dir")

        # output log file
        parser.add_argument('-o', '--out-log', type = str, help = 'Out-file for logs. Default is \
                \'etherblob_{start block}-{end block}.log\'.', default = "default_log_file")

        # save all transactions and their info
        parser.add_argument('-s', '--save-transactions', action = 'store_true', help = 'If enabled, all \
                transactions and their info are stored at file \
                \'transactions_{start-block}-{end-block}.txt\'')

        # ignored file formats
        parser.add_argument('-i', '--ignored-fmt',  help = 'Ignored file formats for extraction. \
                Default ignored/common file formats are \'ISO-8859 text\' and \'Non-ISO extended-ASCII \
                text\'. The \'data\' file format is always ignored. Accepts file format substrings and \
                makes case-insensitive matches. \'*\' is a wildcard to ignore all file formats.', \
                nargs = '*', default = ["default_file_fmt"])

        # print version and exit
        parser.add_argument('--version', action = 'version', version = f'EtherBlob Explorer {etherblob.__version__}')

        return parser.parse_args()
