
# Simple check of the seq2seq coref data:
# Reads in input and output sequences. Removes coreference annotation tokens from output sequences, what remains should be identical to the input sequences.

import sys
from fairseq.globals import EOD_marker, coref_mention_start, coref_mention_end, coref_cluster_sep, coref_cluster_pref

f = open(sys.argv[1], encoding='utf-8')
ill = f.readlines()
f.close()

f = open(sys.argv[2], encoding='utf-8')
oll = f.readlines()
f.close()

assert len(ill) == len(oll)

for idx in range(len(ill)):
    il = ill[idx].strip()

    ott = oll[idx].strip().split()
    clean_ott = []
    for t in ott:
        if t not in [coref_mention_start, coref_mention_end, coref_cluster_sep] and coref_cluster_pref not in t:
            clean_ott.append( t )

    assert il == ' '.join(clean_ott), ' - missmatch:\n * {}\n vs.\n * {}'.format(il, ' '.join(clean_ott))

print(' - Check passed.')

