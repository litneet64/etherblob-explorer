import etherblob
from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='etherblob-explorer',
    version=etherblob.__version__,
    description='Search and extract blob files on the Ethereum Blockchain network',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/litneet64/etherblob-explorer',
    author='litneet64',
    author_email='litneet64@gmail.com',
    license='MIT',
    packages=['etherblob',
              'etherblob.lib',
              'etherblob.utils'
              ],
    entry_points={
        "console_scripts": [
            "etherblob = etherblob:main"
        ]
    },
    install_requires=['argparse',
                      'etherscan-python',
                      'python-magic',
                      'binwalk@git+https://github.com/ReFirmLabs/binwalk.git',
                      'pyfiglet',
                      'termcolor'
                      ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
