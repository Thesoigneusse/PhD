
import os
import sys

import coref_data_utils
from fairseq.globals import EOD_marker, coref_mention_start, coref_mention_end, coref_cluster_sep, coref_cluster_pref

# Example data format of CoNLL 2012 Shared task data
'''#begin document (wb/a2e/00/a2e_0001); part 000
wb/a2e/00/a2e_0001   0    0             A     DT   (TOP(S(NP*           -    -   -   -        *   (ARG0*              *              *       (0
wb/a2e/00/a2e_0001   0    1         Saudi     JJ            *           -    -   -   -    (NORP)       *              *              *        -
wb/a2e/00/a2e_0001   0    2         woman     NN            *)       woman   -   -   -        *        *)             *              *        0)
wb/a2e/00/a2e_0001   0    3        issues    VBZ         (VP*        issue  01   1   -        *      (V*)             *              *        -
wb/a2e/00/a2e_0001   0    4             a     DT      (NP(NP*           -    -   -   -        *   (ARG1*     (ARGM-LOC*     (ARGM-LOC*       (7
wb/a2e/00/a2e_0001   0    5         voice     NN            *        voice   -   1   -        *        *              *              *        -
wb/a2e/00/a2e_0001   0    6     recording     NN            *)   recording   -   1   -        *        *              *)             *)       -
wb/a2e/00/a2e_0001   0    7            in     IN  (SBAR(WHPP*           -    -   -   -        *        *   (R-ARGM-LOC*   (R-ARGM-LOC*        -
wb/a2e/00/a2e_0001   0    8         which    WDT      (WHNP*))          -    -   -   -        *        *              *)             *)       -
wb/a2e/00/a2e_0001   0    9           she    PRP       (S(NP*)          -    -   -   -        *        *         (ARG0*)        (ARG0*)      (0)
wb/a2e/00/a2e_0001   0   10        mourns    VBZ      (VP(VP*        mourn  01   -   -        *        *            (V*)             *        -
wb/a2e/00/a2e_0001   0   11           her   PRP$         (NP*           -    -   -   -        *        *         (ARG1*              *    (3|(0)
wb/a2e/00/a2e_0001   0   12       brother     NN           *))          -    -   -   -        *        *              *)             *        3)
wb/a2e/00/a2e_0001   0   13           and     CC            *           -    -   -   -        *        *              *              *        -
wb/a2e/00/a2e_0001   0   14       demands    VBZ         (VP*       demand  01   1   -        *        *              *            (V*)       -
wb/a2e/00/a2e_0001   0   15           the     DT      (NP(NP*           -    -   -   -        *        *              *         (ARG1*        -
wb/a2e/00/a2e_0001   0   16    punishment     NN            *)          -    -   -   -        *        *              *              *        -
wb/a2e/00/a2e_0001   0   17            of     IN         (PP*           -    -   -   -        *        *              *              *        -
wb/a2e/00/a2e_0001   0   18           his   PRP$         (NP*           -    -   -   -        *        *              *              *       (3)
wb/a2e/00/a2e_0001   0   19       killers    NNS    *)))))))))          -    -   -   -        *        *)             *              *)       7)
wb/a2e/00/a2e_0001   0   20             .      .           *))          -    -   -   -        *        *              *              *        -'''


def conll_to_seq2seq_format(input_seq, conll_output_seq):

    open_m = coref_mention_start
    close_m = coref_mention_end
    cluster_sep = coref_cluster_sep
    cluster_pref = coref_cluster_pref

    assert len(input_seq) == len(conll_output_seq)
    seq2seq_sequence = []
    open_clusters = [] 
    for idx, t in enumerate(conll_output_seq):
        tt = t.split('|')
        if len(tt) == 1:
            if '(' in t and ')' in t:
                seq2seq_sequence.extend( [open_m, input_seq[idx], cluster_sep, cluster_pref +  t[t.index('(')+1:t.index(')')], close_m] )
            elif '(' in t:
                seq2seq_sequence.extend( [open_m, input_seq[idx]] )
                open_clusters.append( t[1:] )
            elif ')' in t:
                cluster_id = t[:-1]
                found = False
                for oc_idx, oc in enumerate(open_clusters):
                    if oc == cluster_id:
                        found = True
                        del open_clusters[oc_idx]
                        break
                if not found:
                    raise ValueError('Found closing cluster mark for {}, but no opening mark was found'.format(cluster_id))
                seq2seq_sequence.extend( [input_seq[idx], cluster_sep, cluster_pref + cluster_id, close_m] )
            elif t == '-':
                seq2seq_sequence.append( input_seq[idx] )
            else:
                raise ValueError('Unexpected token {} in conll output sequence'.format(t))
        else:
            nopen = 0
            nclose = 0
            for c in t:
                if c == '(':
                    nopen += 1
                if c == ')':
                    nclose += 1
            assert nopen != nclose, 'parse error at {}'.format(t)

            if nopen > nclose:  # opening pattern
                if nclose > 0:
                    assert t[-1] == ')', 'open pattern parse error at {}'.format(t)

                for tok_idx, tok in enumerate(tt):
                    if '(' in tok and ')' in tok:
                        seq2seq_sequence.extend( [open_m, input_seq[idx], cluster_sep, cluster_pref +  tok[tok.index('(')+1:tok.index(')')], close_m] )
                    elif '(' in tok:
                        seq2seq_sequence.append( open_m )
                        open_clusters.append( tok[1:] )
                    elif ')' in tok or '-' in tok:
                        raise ValueError('Opening pattern parse error at {}'.format(t))
                if nclose == 0:
                    seq2seq_sequence.append( input_seq[idx] )
            else:   # closing pattern
                if nopen > 0:
                    assert t[0] == '(', 'close pattern parse error at {}'.format(t)

                if nopen == 0:
                    seq2seq_sequence.append( input_seq[idx] )
                for tok_idx, tok in enumerate(tt):
                    if '(' in tok and ')' in tok:
                        seq2seq_sequence.extend( [open_m, input_seq[idx], cluster_sep, cluster_pref +  tok[tok.index('(')+1:tok.index(')')], close_m] )
                    elif ')' in tok:
                        cluster_id = tok[:-1]
                        found = False
                        for oc_idx, oc in enumerate(open_clusters):
                            if oc == cluster_id:
                                found = True
                                del open_clusters[oc_idx]
                                break
                        if not found:
                            raise ValueError('Found closing cluster mark for {}, but no opening mark was found'.format(cluster_id))
                        seq2seq_sequence.extend( [cluster_sep, cluster_pref + cluster_id, close_m] )        
                    elif '(' in tok or '-' in tok:
                        raise ValueError('Closing pattern parse error at {}'.format(t))

    assert len(open_clusters) == 0, 'Found unclosed clusters: {}'.format(' '.join(open_clusters))

    #print('[DEBUG] conll_to_seq2seq_format,\n\tgot conll sequence: {}\n\tgenerated seq2seq sequence: {}'.format(' '.join(conll_output_seq), ' '.join(seq2seq_sequence)))
    #sys.stdout.flush()

    return seq2seq_sequence

def main(args):

    with open(args[1], 'r', encoding='utf-8') as f:
        lines = [l.rstrip() for l in f.readlines()]
        f.close()

    data = []
    for filename in lines:
        file_data = coref_data_utils.read_tabular_data( filename )
        for did in file_data.keys():
            file_data[did]['max_seg'] = {}
            for k, mm in file_data[did]['mentions'].items():

                ms, flag = coref_data_utils.compute_maximal_segmentations(mm)
                ms_out = coref_data_utils.get_maximal_segmentation_output(len(file_data[did]['sentences'][k]), ms)
                assert k not in file_data[did]['max_seg']
                file_data[did]['max_seg'][k] = ms_out
        data.append(file_data)

    final_data = []
    for ee in data:
        for did in ee.keys():
            input_seqs = ee[did]['sentences']
            conll_seqs = ee[did]['coref_seqs']
            output_seqs = []
            for idx, cs in enumerate(conll_seqs):
                seq2seq_seq = conll_to_seq2seq_format(input_seqs[idx], cs)
                output_seqs.append( seq2seq_seq )

                # TMP for Debug
                #if idx >= 10:
                #    sys.exit(0)

            assert len(input_seqs) == len(output_seqs)

            if len(input_seqs) > 0:
                print(' - Read {} sequences from document {}'.format(len(input_seqs), did))
                sys.stdout.flush()

                final_data.append( (input_seqs, output_seqs) )
            else:
                print(' * WARNING: read empty file @ID {}'.format(did))
                sys.stdout.flush()
 
    input_sequence_file = args[1] + '.input'
    output_sequence_file = args[1] + '.output'
    fi = open(input_sequence_file, 'w', encoding='utf-8')
    fo = open(output_sequence_file, 'w', encoding='utf-8')
    for tt in final_data:
        for iseq, oseq in zip(tt[0], tt[1]):
            fi.write(' '.join(iseq) + '\n')
            fo.write(' '.join(oseq) + '\n')
        fi.write(EOD_marker + '\n')
        fo.write(EOD_marker + '\n')
    fi.close()
    fo.close()

if __name__ == '__main__':
    main(sys.argv)

