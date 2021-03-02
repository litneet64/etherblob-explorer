# EtherBlob Explorer
![GitHub top language](https://img.shields.io/github/languages/top/litneet64/etherblob-explorer) ![GitHub](https://img.shields.io/github/license/litneet64/etherblob-explorer)

Search and extract blob files on the Ethereum network using [Etherscan.io](https://etherscan.io/apis) API.

## Introduction
EtherBlob Explorer is a tool intended for researchers, analysts, CTF players or anyone curious enough wanting to search for different kinds of files or any meaningful human-supplied data on the Ethereum Blockchain Network. It searches over a user-supplied range of block IDs or UNIX timestamps.

 For a real-life case you can read [this](https://boobies.surge.sh/) experiment made on 2017. The immutability of the blockchain can truly be a double-edged sword.

## Features

### Search Locations

This tool can search on the following locations, either separately or combining any of these on the same run:

* **Transaction Input Data**: search inside transaction's input data (default location).
* **Block Input Data**: search inside block's input data.
* **To Addresses**: search appending 'to' addresses as the possible input **[*]** (checking first for file headers and re-checking when all data is harvested using binwalk).

**[\*]** Storing data on 'to' addresses is possible on the Ethereum network as there's no verification if sending to an address that has no associated account keys. Meaning you can make transactions to arbitrary addresses to craft a payload over several 20-byte sized transactions (it's very rare but so are some CTF challenges).

### Search and Extraction Methods

All of these methods can be used either separately or in any combination:

* **Embedded Files**: search for files embedded inside data using `binwalk`.
* **File Headers / Magic Bytes**: search using headers + magic bytes via levaraging the Linux util `file` (default method).
* **ASCII String Dump**: search for ASCII strings inside data.
* **Entropy-Based Search**: use Shannon's Entropy as a measure tool to search for natural language text (e.g. UTF-8 Unicode), encrypted/compressed files or anything the user seems viable with user-supplied entropy limits.

**IMPORTANT**: The order showed here is used _under-the-hood_ for discarding searches with other methods (e.g. if file is found via `embedded files` then it won't attempt to search using `file headers`, `ascii string dump` nor `entropy` as it's not likely to find anything meaningful if previous methods were already successful).

### Misc

* Accepts UNIX timestamps (instead of block IDs) that get resolved into the closest block IDs commited at those times.
* Save all data from visited transactions into file for later reviewing.
* Store CLI-displayed logs into file for later extracted-file analysis.
* Ignore user-supplied file formats (case-insensitive) for extraction and accepts substrings of the complete file format for blacklisting.
* Print general progress metrics (e.g. how many blocks / transactions have been parsed, how many blocks are left) every minute and also display some interesting metrics at the end of the current run.
* More useful features found on the manual (`-h`)!

## Usage

### Common use cases
Standard search (look inside transactions via file headers) with API key on default location (`.api-key`):
```bash
litneet64@mach-5:~$ ./etherblob.py 4081599 4081600
```

More "in-through" search (search for embedded files + regular search method) with key inside arbitrary file:
```bash
litneet64@mach-5:~$ ./etherblob.py -K api.key 4081599 4081600 -M
```

Search over block headers and transactions at the same time and save extracted files to 'extracted':
```bash
litneet64@mach-5:~$ ./etherblob.py 4081599 4081600 --blocks --transactions -D extracted/
```

Search only inside 'to' addresses in range from blocks commited between `Jan 25 2021 19:00:00` and `Jan 26 2021 19:00:00`:
```bash
litneet64@mach-5:~$ ./etherblob.py -t 1611601200 1611687600 --addresses
```

Search only inside transactions for encrypted/compressed data (ignoring any other file format):
```bash
litneet64@mach-5:~$ ./etherblob.py 4081599 4081600 --encrypted -i '*'
```

Search inside transactions for custom entropy files (if file-header search doesn't find a thing) while saving transactions into file:
```bash
litneet64@mach-5:~$ ./etherblob.py  3911697 3912697 -E 4.0 5.0 -s
```

Only dump ASCII strings over blocks and transactions made on Christmas Eve (between the 24th and 25th):
```bash
litneet64@mach-5:~$ ./etherblob.py -t 1608836400 1608922800 --blocks --transactions --strings -i '*'
```

Full-blown search (expect many false-positives):
```bash
litneet64@mach-5:~$ ./etherblob.py 4081599 4081600 -U -S -M --blocks --transactions --addresses
```



### Manual
```
usage: etherblob.py [-h] [--transactions] [--blocks] [--addresses] [-M] [-U] [-E CUSTOM_ENTROPY CUSTOM_ENTROPY] [--encrypted] [-S]
                    [-t] [-K API_KEY_PATH] [-k API_KEY] [-D OUTPUT_DIR] [-o OUT_LOG] [-s] [-i [IGNORED_FMT ...]] [--version]
                    start_block end_block

Tool to search and extract blob files on the Ethereum Network.

positional arguments:
  start_block           Start of block id range.
  end_block             End of block id range.

optional arguments:
  -h, --help            show this help message and exit
  --transactions        Search for blob files on transaction inputs. Default search mode.
  --blocks              Search for blob files on block inputs. If enabled then transaction input check is disabled unless explicitly
                        enabled.
  --addresses           Search for blob files on 'to' transaction addresses, as on Ethereum anyone can make transactions to an
                        arbitrary address even if it has no related owner (still not very common). If enabled then transaction's input
                        check is disabled unless explicitly enabled.
  -M, --embedded        If enabled, search for embedded files on data (from blocks, transactions or addresses) via binwalk. Disabled
                        by default as parsing now takes longer.
  -U, --unicode         If enabled, attempt to search and dump files containing UTF-8 text from harvested data (blocks, transactions,
                        addresses) using Shannon's Entropy (between 3.5 and 5.0) if no other discernible file is found first on that
                        data. Yields many false positives.
  -E CUSTOM_ENTROPY CUSTOM_ENTROPY, --custom-entropy CUSTOM_ENTROPY CUSTOM_ENTROPY
                        Define your own entropy limits (min and max) to search for files/data on harvested data.
  --encrypted           If enabled, attempt to search and dump encrypted/compressed data found via different search methods (blocks,
                        transactions, addresses) using Shannon's Entropy (between 7.0 and 8.0) if no other discernible file is found
                        first on that data.
  -S, --strings         If enabled, attempt to search and dump ASCII strings into files found inside harvested data (blocks,
                        transactions, addresses) if no other discernible file is found first on that data.
  -t, --timestamps      If enabled, then start and end block IDs are interpreted as UNIX timestamps that are then resolved to the
                        closest commited blocks for those specific times.
  -K API_KEY_PATH, --api-key-path API_KEY_PATH
                        Path to file with Etherscan API key for queries. Default search location is '.api-key'.
  -k API_KEY, --api-key API_KEY
                        Etherscan API key as parameter. If given then '--api-key-path' is ignored.
  -D OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Out-dir for extracted files. Default is 'ext_{start block}-{end block}'.
  -o OUT_LOG, --out-log OUT_LOG
                        Out-file for logs. Default is 'etherblob_{start block}-{end block}.log'.
  -s, --save-transactions
                        If enabled, all transactions and their info are stored at file 'transactions_{start-block}-{end-block}.txt'
  -i [IGNORED_FMT ...], --ignored-fmt [IGNORED_FMT ...]
                        Ignored file formats for extraction. Default ignored/common file formats are 'ISO-8859 text' and 'Non-ISO
                        extended-ASCII text'. The 'data' file format is always ignored. Accepts file format substrings and makes case-
                        insensitive matches. '*' is a wildcard to ignore all file formats.
  --version             show program's version number and exit

Official GitHub repo 'https://github.com/litneet64/etherblob-explorer'
```
