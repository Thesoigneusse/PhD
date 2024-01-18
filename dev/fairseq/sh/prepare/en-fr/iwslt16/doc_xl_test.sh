#!/usr/bin/env bash
# Previous to this script, you should already have run
# sh/preprocess_iwslt16_fr_en_doc.sh

# Move to ./data directory
cd data

# Setting variables
src=fr
tgt=en
lang=fr-en
prep=iwslt16.dnmt.$src-$tgt
outdir=xl_test
tmp=$prep/$outdir/tmp

HEADS=../scripts/retrieve_doc_heads.py
BPEROOT=subword-nmt/subword_nmt
BPE_CODE=$prep/standard/code

rm -rf data-bin/$prep/$outdir
mkdir -p data-bin/$prep/$outdir
mkdir -p $tmp

echo "Assembling test data"
for l in $src $tgt; do
    # textual datasets 
    cat $prep/standard/tmp/IWSLT16.TED.tst2010.fr-en.$l \
        $prep/standard/tmp/IWSLT16.TED.tst2011.fr-en.$l \
        $prep/standard/tmp/IWSLT16.TED.tst2012.fr-en.$l \
        $prep/standard/tmp/IWSLT16.TED.tst2013.fr-en.$l \
        $prep/standard/tmp/IWSLT16.TED.tst2014.fr-en.$l > $tmp/$outdir.$l
    # retrieve indices of headlines
    python $HEADS $tmp/$outdir.$l
    cp $tmp/$outdir.$l.heads data-bin/$prep/$outdir/test.$lang.$l.heads
done

# applying BPE to test data
for l in $src $tgt; do
    f=$outdir.$l
    echo "Apply_bpe.py to ${f}..."
    python $BPEROOT/apply_bpe.py -c $BPE_CODE < $tmp/$f > $prep/$outdir/$f
done

echo "Binarizing data..."
fairseq-preprocess \
    --source-lang $src \
    --target-lang $tgt \
    --testpref $prep/$outdir/$outdir \
    --srcdict data-bin/$prep/standard/dict.en.txt \
    --joined-dictionary \
    --destdir data-bin/$prep/$outdir