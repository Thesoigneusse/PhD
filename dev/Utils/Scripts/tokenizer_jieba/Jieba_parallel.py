import jieba
import sys

import argparse

parser = argparse.ArgumentParser(description="Clean data of WMT23",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-a", "--archive", action="store_true",
                    help="archive mode")
parser.add_argument("-v", "--verbose", action="store_true",
                    help="increase verbosity")
parser.add_argument("-i", "--input-path", help="Input PATH")
parser.add_argument("-o", "--output-path", help="Output PATH")
args = parser.parse_args()
config = vars(args)

jieba.enable_parallel()
url = config['input_path']
content = open(url, "rb").read()
words = " ".join(jieba.cut(content))

log_f = open(config["output_path"], "wb")
log_f.write(words.encode('utf-8'))
