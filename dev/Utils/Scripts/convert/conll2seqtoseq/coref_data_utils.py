
import os
import sys
import re

from typing import List

_CHECK_ = True
_DEBUG_ = False

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

def merge_clusters_(cluster1, cluster2, debug_flag=False):

    for e_id in cluster1:
        if e_id in cluster2:

            if debug_flag:
                raise ValueError('Found cross document clusters')

            if cluster1[e_id][0][0] != cluster2[e_id][0][0]:    # NOTE: assuming clusters contains entities of a whole document
                cluster1[e_id].extend( cluster2[e_id] )
                del cluster2[e_id]
            else:
                raise ValueError('Processing error, the clusters to be merged are either the same cluster or there is an error in the doc_id their mention contain')

def read_tabular_data(filename, tk_idx=3, cr_idx=-1, delimiter='\t', keep_columns: List=None):
    """
    Reads the data in 'filename', expected to be in the tabular format above.
    Since each file may contain more than one document, delimited the '#begin document' marker, the returned data structure may contain logically more than one document.
    The returned data structure is a hash table where the key is the document ID, the value is a dictionary with the following fields:
     - 'nsents': the total number of sentences in the document
     - 'ntoks': the total number of tokens in the document
     - 'clusters': a hash table where the key is the cluster (or entity) ID, e.g. with annotation (3) the cluster ID is 3, the value is the list of mentions in the cluster, in this document.
                    Mentions are represented as tuples containing: document ID, sentence ID, absolute start-token index, absolute end-token index, relative start-token index, and relative end-token index.
                    Relative indexes are with respect to the document. That is, the first token of each document has index 0, while the absolute token index is different, except for the first document.
                    Example of a tuple: (doc_id, sent_id, tok_id, tok_id, doc_tok_id, doc_tok_id) 
     - 'mentions': a hash table where the key is the sentence ID, the value is the list of mentions in that sentence.
                    Mentions are represented as tuples containing: 
                    Example of a tuple: (e_id, doc_id, sent_id, tok_id, tok_id, doc_tok_id, doc_tok_id)
     - 'sentences': the list of sentences in this document. Each sentence is a list of tokens.
     - 'coref_seqs': the list of sequences (sentences) annotated with coreferences, as represented in the last column of the document. Each sequence is a list of tokens.
     - 'mention2cluster': a hash table where the key is a uniq mention ID made of the concatenation of document ID, sentence ID, absolute start-token, and absolute end-token ID,
                            the value is the cluster ID the mention belong to.
                            Example of mention key: str(doc_id) + '-' + str(sent_id) + '-' + str(tok_id) + '-' + str(tok_id)
    """

    gold_doc_idx = 1
    gold_tok_idx = 2

    sp_re = re.compile('\s+')

    f = open(filename, encoding='utf-8')
    ll = f.readlines()
    f.close()

    fdid = ''
    doc_id = sent_id = doc_tok_id = tok_id = e_id = 0   # Respectively: Document ID (basically an index), sentence ID (basically an index), document-level index, sentence-level index, Entity (or cluster) ID.
    mention_start = mention_end = -1    # States for indicating a mention opening/closing has been encountered.
    open_clusters = []      # Keeps open mentions, with their cluster ID (i.e. entity or coreference chain ID if you like), for which we have not yet read the closing marker.

    data = {}               # Keeps coreference data for each document
    clusters = {}           # Cluster set for the current document, given an Entity ID, it returns the list of mentions in that entity.
                            #       Mentions are stored as tuples with: document ID, sentence ID, starting and ending token index in the sentence, starting and ending token index in the document.
    mentions = {}           # Mention set for the current document, given a sentence ID, it returns the list of mentions in that sentence.
                            #       Mentinos are stored as tuples with: cluster ID, document ID, starting and ending token index in the sentence, starting and ending token index in the document.
    #mentions_by_id = {}
    mention2cluster = {}    # Map from mention to the entity it belongs to
    sentences = []  # NOTE: input (sentences are lists of tokens)
    coref_seqs = [] # NOTE: final output
    curr_sent = []
    coref_seq = []
    for l in ll:
        if '#begin document' in l:  # we read a new document begin marker: we finalize the current document and we reset all the data structures

            #print('[DEBUG] got begin of document mark')
            #sys.stdout.flush()

            if len(sentences) > 0:
                assert fdid != ''
                did = fdid + '-' + str(doc_id)
                if did in data:
                    raise ValueError()
                data[did] = {'nsents': sent_id, 'ntoks': doc_tok_id, 'clusters': clusters, 'mentions': mentions, 'sentences': sentences, 'coref_seqs': coref_seqs, 'mention2cluster': mention2cluster}
                doc_id += 1

            sent_id = doc_tok_id = tok_id = e_id = 0
            mention_start = mention_end = 0
            clusters = {}
            mentions = {}
            mention2cluster = {}
            sentences = []
            coref_seqs = []
            curr_sent = []
            coref_seq = []
        elif '#end document' in l:  # we read an end of document marker: we finalize the current document and we reset all the data structures

            #print('[DEBUG] got end of document mark')
            #sys.stdout.flush()

            if len(sentences) > 0:
                assert fdid != ''
                did = fdid + '-' + str(doc_id)
                if did in data:
                    raise ValueError()
                data[did] = {'nsents': sent_id, 'ntoks': doc_tok_id, 'clusters': clusters, 'mentions': mentions, 'sentences': sentences, 'coref_seqs': coref_seqs, 'mention2cluster': mention2cluster}
                doc_id += 1

            sent_id = doc_tok_id = tok_id = e_id = 0
            mention_start = mention_end = 0
            clusters = {}
            mentions = {}
            mention2cluster = {}
            sentences = []
            coref_seqs = []
            curr_sent = []
            coref_seq = []
        else:
            l = re.sub('\s+', '\t', l.rstrip())
            tt = l.split(delimiter) 

            if len(tt) == 0 or (len(tt) == 1 and tt[0] == ''):  # Empty line ? Then that's the end of a sentence and the mentions it contains
                if len(open_clusters) > 0:  # mentions spanning multiple sentences are not allowed!
                    raise ValueError( 'Unmatched opening mentions (cluster-id, mention start idx): {}'.format(open_clusters) )
                sentences.append(curr_sent)
                coref_seqs.append(coref_seq)
                sent_id += 1
                tok_id = 0
                curr_sent = []
                coref_seq = []
            else:

                #print('[DEBUG] processing: {}'.format(tt))
                #sys.stdout.flush()

                assert len(tt[tk_idx]) > 0
                assert len(tt[cr_idx]) > 0

                fdid = tt[0]
                curr_sent.append( tt[tk_idx] )      # Store the current token (column 4 by default) for the current sentence
                coref_seq.append( tt[cr_idx] )      # Store the coreference info (last column of the file by default)
                coref_info = tt[cr_idx]
                if coref_info != '-':               # '-' means "it is not in a mention" or "it is in a previously opened mention". It current token is not '-' some new coref info must be processed
                    clust_info = coref_info.split('|')
                    for cc in clust_info:
                        if '(' in cc and ')' in cc:     # Simplest case: the mention opens and closes in the same line (only 1 token)

                            assert int(tt[gold_doc_idx]) == doc_id, 'Missmatching gold and computed doc id ({} vs. {})'.format(tt[gold_doc_idx], doc_id)
                            assert int(tt[gold_tok_idx]) == tok_id, 'Missmatching gold and computed token id ({} vs. {})'.format(tt[gold_tok_idx], tok_id)

                            e_id = cc[1:-1]     # Entity ID: we remove ( and )
                            if e_id not in clusters:
                                clusters[e_id] = []
                            clusters[e_id].append( (doc_id, sent_id, tok_id, tok_id, doc_tok_id, doc_tok_id) )      # we add the current mention in the corresponding cluster info
                            if sent_id not in mentions:
                                mentions[sent_id] = []
                            mentions[sent_id].append( (e_id, doc_id, sent_id, tok_id, tok_id, doc_tok_id, doc_tok_id) )      # we add the current mentions in the corresponding sentence info
                            mkey = str(doc_id) + '-' + str(sent_id) + '-' + str(tok_id) + '-' + str(tok_id)     # the unique key for a mention: concatenation of document ID, sentence ID, starting and ending token idx.
                            '''if mkey in mentions_by_id:
                                raise ValueError('Clash with mention {} at {}'.format(mkey, filename))
                            mentions_by_id[mkey] = (doc_id, sent_id, tok_id, tok_id)'''
                            if mkey in mention2cluster:
                                raise ValueError('Clash with mention {} at {}'.format(mkey, filename))      # mention keys must be unique by definition !
                            mention2cluster[mkey] = e_id        # we add the current mention to the map mention -> entity ID
                        elif '(' in cc:     # we read an opening mention marker, we store this partial information in the open_clusters data structure, waiting for the matching closing marker.
                            e_id = cc[1:]
                            open_clusters.append( (e_id, tok_id, doc_tok_id) )
                        elif ')' in cc:     # we read a closing mention marker, we look for the matching opening marker in the open_clusters data structure.
                            e_id = cc[:-1]

                            #print('[DEBUG] got cluster id {}, current open clusters: {}'.format(e_id, open_clusters))
                            #sys.stdout.flush()

                            if len(open_clusters) == 0:
                                raise ValueError('Found unmatched closing cluster {}'.format(e_id))

                            found = False
                            t_idx = -1
                            match = ()
                            for oc_idx in range(len(open_clusters)-1,-1,-1):    # we search open_clusters backward, as mentions could be nested
                                tpl = open_clusters[oc_idx]
                                if tpl[0] == e_id:
                                    match = tpl
                                    t_idx = oc_idx
                                    found= True
                                    break

                            if len(match) == 0:     # No match found: data format problem or maybe this script is not completly correct...
                                raise ValueError('Parsing error, closing cluster id {} not found in file {}'.format(e_id, filename))
                            else:
                                if e_id not in clusters:
                                    clusters[e_id] = []
                                assert tok_id >= match[1]
                                assert doc_tok_id >= match[2]
                                clusters[e_id].append( (doc_id, sent_id, match[1], tok_id, match[2], doc_tok_id) )      # we store the current mention in the cluster data structure
                                if sent_id not in mentions:
                                    mentions[sent_id] = []
                                mentions[sent_id].append( (e_id, doc_id, sent_id, match[1], tok_id, match[2], doc_tok_id) )     # we store the current mention in the sentence data structure

                                mkey = str(doc_id) + '-' + str(sent_id) + '-' + str(match[1]) + '-' + str(tok_id)
                                '''if mkey in mentions_by_id:
                                    raise ValueError('Clash with mention {} at {}'.format(mkey, filename))
                                mentions_by_id[mkey] = (doc_id, sent_id, tok_id, tok_id)'''
                                if mkey in mention2cluster:
                                    raise ValueError('Clash with mention {} at {}'.format(mkey, filename))
                                mention2cluster[mkey] = e_id

                            #print('[DEBUG] deleting open cluster entry {}'.format(t_idx))

                            assert t_idx != -1
                            del open_clusters[t_idx]

                            #print('[DEBUG] updated open clusters: {}'.format(open_clusters))
                            #sys.stdout.flush()
                        else:
                            raise ValueError('Unrecognized coreference annotatin format: {}'.format(cc)) 

                tok_id += 1
                doc_tok_id += 1

    if len(open_clusters) > 0:
        raise ValueError( 'Unmatched opening mentions (cluster-id, mention start idx): {}'.format(open_clusters) )

    if len(sentences) > 0:
        print('File is missing <#end document> mark, closing automatically')
        sys.stdout.flush()

        assert fdid != ''
        did = fdid + '-' + str(doc_id)
        if did in data:
            raise ValueError()
        data[did] = {'nsents': sent_id, 'ntoks': doc_tok_id, 'clusters': clusters, 'mentions': mentions, 'sentences': sentences, 'coref_seqs': coref_seqs, 'mention2cluster': mention2cluster}

    '''d_keys = list(data.keys())
    for k1_idx in range(len(d_keys)-1):
        for k2_idx in range(k1_idx+1,len(d_keys)):
            k1 = d_keys[k1_idx]
            k2 = d_keys[k2_idx]
            print(' * Merging (possibly) clusters in documents {} - {}'.format(k1, k2))
            sys.stdout.flush()
            merge_clusters_(data[k1]['clusters'], data[k2]['clusters'])'''

    if _CHECK_:
        for dk in data.keys():
            for k in data[dk]['clusters'].keys():
                for m in data[dk]['clusters'][k]:
                    assert len(m) == 6
                    assert m[2] <= m[3]
                    assert m[4] <= m[5]

            for k in data[dk]['mentions'].keys():
                for m in data[dk]['mentions'][k]:
                    assert len(m) == 7
                    assert m[3] <= m[4]
                    assert m[5] <= m[6]

    if _DEBUG_:
        print('[DEBUG] summary:') 
        print('[DEBUG]    * read {} documents'.format(len(data)))
        clsts = 0
        sents = 0
        toks = 0
        mnts = cl_mnts = 0
        for dk in data.keys():
            print('[DEBUG]      * # sentences and # tokens @ doc {}: {}, {}'.format(dk, data[dk]['nsents'], data[dk]['ntoks']))
            mnts += sum([len(data[dk]['mentions'][k]) for k in data[dk]['mentions'].keys()])
            cl_mnts += sum([len(data[dk]['clusters'][k]) for k in data[dk]['clusters'].keys()])
            clsts += len(data[dk]['clusters'])
            sents += len(data[dk]['sentences'])
            assert len(data[dk]['sentences']) == data[dk]['nsents']
            toks += data[dk]['ntoks']
        assert mnts == cl_mnts
        print('[DEBUG]    * found {} mentions'.format(mnts))
        print('[DEBUG]    * found {} clusters: '.format(clsts))
        #for dk in data.keys():
        #    print( ' *** {}'.format(data[dk]['clusters'].keys()))
        print('[DEBUG]    * read {} sentences'.format(sents))
        print('[DEBUG]    * total num of tokens: {}'.format(toks))
        print(' -----')
        sys.stdout.flush()

    return data

def compute_maximal_segmentations(mentions):

    def mention_overlap(m1, m2):

        assert m1[3] != m2[3] or m1[4] != m2[4]
        if m1[3] <= m2[3] and m1[4] >= m2[4]:    # NOTE: case1 (1 (2 )2 )1
            return True
        elif m1[3] >= m2[3] and m1[4] <= m2[4]:  # NOTE: case2 (2 (1 )1 )2
            return True
        elif m1[3] <= m2[3] and m1[4] >= m2[3]:  # NOTE: case3 (1 (2 )1 )2
            return True
        elif m1[3] <= m2[4] and m1[4] >= m2[4]:  # NOTE: case4 (2 (1 )2 )1
            return True
        else:
            return False
 
    overlaps = []
    w_flag = False
    for ii in range(len(mentions)):
        if len(overlaps) == 0:
            overlaps.append( list(mentions[ii]) )
        else:
            found = False
            for m in overlaps:
                if mention_overlap(mentions[ii], m) and not found:
                    if mentions[ii][3] < m[3]:
                        m[3] = mentions[ii][3]
                    if mentions[ii][4] > m[4]:
                        m[4] = mentions[ii][4]
                    found = True
                elif mention_overlap(mentions[ii], m):
                    if mentions[ii][3] < m[3]:
                        m[3] = mentions[ii][3]
                    if mentions[ii][4] > m[4]:
                        m[4] = mentions[ii][4]
                    w_flag = True
                    #print('compute_maximal_segmentation WARNING: mention {} has several overlapping clusters! (overlaps: {})'.format(mentions[ii], overlaps))
                    #sys.stdout.flush()
            if not found:
                overlaps.append( list(mentions[ii]) )

    if len(overlaps) > 0:
        overlaps = sorted(overlaps, key=lambda tuple: tuple[3])

    return overlaps, w_flag

    '''m_keys = mentions.keys()
    overlapping_clusters = []
    m2c = {}
    for k in mentions.keys():
        sent_ment = mentions[k]
        for i in range(len(sent_ment)-1):
            not_overlapping = True
            for j in range(i+1,len(sent_ment)):
                # TODO: RESTART WORKING FROM HERE
                if mention_overlap(sent_ment[i], sent_ment[j]):
                    not_overlapping = False
                    if i in m2c and j not in m2c:
                        m2c[j] = m2c[i]
                        overlapping_clusters[m2c[j]].append(j)
                    elif j in m2c and i not in m2c:
                        m2c[i] = m2c[j]
                        overlapping_clusters[m2c[i]].append(i)
                    else:
                        m2c[i] = len(overlapping_clusters)
                        m2c[j] = len(overlapping_clusters)
                        overlapping_clusters.append([])
                        overlapping_clusters[m2c[i]].extend( [i, j] )

    # Step 2: compute maximum span of each cluster

    # Step 3: add non-overlapping mentions and compute maximum span for each sentence'''

def get_maximal_segmentation_output(sent_len, max_segs):

    res = []
    for i in range(sent_len):

        label = 'O'
        for m in max_segs:
            if i == m[3]:
                label = 'B'
            elif i == m[4] and m[3] < m[4]:
                label = 'I'
            elif i > m[3] and i < m[4]:
                label = 'I'
        res.append(label)

    return res

def main(args):

    with open(args[1], 'r', encoding='utf-8') as f:
        lines = [l.rstrip() for l in f.readlines()]
        f.close()

    data = []
    for filename in lines:
        file_data = read_tabular_data( filename )
        for did in file_data.keys():
            file_data[did]['max_seg'] = {}
            for k, mm in file_data[did]['mentions'].items():

                print('[DEBUG] sentence {}: {}'.format(k, file_data[did]['sentences'][k]))
                #print('[DEBUG] computing maximal segmentation of: {}'.format([(m[3], m[4]) for m in mm]))
                #sys.stdout.flush()

                ms, flag = compute_maximal_segmentations(mm)
                ms_out = get_maximal_segmentation_output(len(file_data[did]['sentences'][k]), ms)
                assert k not in file_data[did]['max_seg']
                file_data[did]['max_seg'][k] = ms_out

                print('[DEBUG] maximal segmentation: {}'.format([(m[3], m[4]) for m in ms]))
                print('[DEBUG] maximal segmentation output: {}'.format(ms_out))
                print(' ----------')
                print('')
                sys.stdout.flush()

        data.append(file_data)


if __name__ == '__main__':
    main(sys.argv)
