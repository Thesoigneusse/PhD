import argparse
import os
import re


def main():
    parser = argparse.ArgumentParser(
        description='Take as input a text file with documents separated by an empty line. '
                    'Remove the empty lines separating the documents and write the indices'
                    'of the headlines to a new file. ',
    )
    # fmt: off
    parser.add_argument('input_path',help='Input dataset file paths.')
    parser.add_argument('--fill-size',
        type=int,
        metavar='N',
        default=None,
        help='fill output with artificial heads every fill-size lines'
    )
    parser.add_argument('--regular-expression',
                        type=str,
                        default=None,
                        help='Regular expression to explain the end of the document')
    # fmt: on
    args = parser.parse_args()

    new = args.input_path
    old = args.input_path + '~'
    os.rename( new, old )
    heads_path = new + '.heads'

    heads = [1]
    cnt = 0
    with open(old, 'r') as infile, open(new, 'w+') as outfile:
        for n, line in enumerate(infile):
            if (line.strip() and args.regular_expression is None) \
                or re.fullmatch(args.regular_expression, line) is None : # non-empty line and no regular_expression or not the regular expression that we look for. Write it to output
                outfile.write(line)  
            else:
                id = n + 1 - cnt
                if id != 1 : # first head is added by definition
                    heads.append(id)
                cnt += 1
        

    os.remove(old)

    print("Number of document in {0}: ".format(new), len(heads))
    # print("Their heads are lines: ", heads, end="\n\n")
    if args.fill_size is not None:
        last_head = heads[-1] + args.fill_size
        while last_head <= n:
            heads.append(last_head)
            last_head += args.fill_size
    print("After adding artificial heads: ", len(heads))
    
    with open(heads_path, 'w+') as outfile:
        for h in heads:
            outfile.write(str(h) + '\n')

if __name__ == '__main__':
    main()