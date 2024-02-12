#!/usr/bin/env bash

# src=en
src=input
tgt=output
lang=$src-$tgt
HOME=/home/getalp/lopezfab/PhD
DATA=$HOME/dev/fairseq/data/coreference
# orig=/video/getalp/
orig=$HOME/../temp/orig/coreference/CoNLL-2012


mkdir -p $DATA
cd $DATA

corpus=conll-2012

# Standard variables
TOOLS=../../tools
SCRIPTS=$TOOLS/mosesdecoder/scripts
TOKENIZER=$SCRIPTS/tokenizer/tokenizer.perl
BPEROOT=$TOOLS/subword-nmt/subword_nmt

CLEAN=../../scripts/clean-corpus-n-leaving-blanks.perl
HEADS=../../scripts/retrieve_doc_heads.py

if [ $1 = "standard" ]; then
    prep=$corpus/standard
    tmp=$prep/tmp
    mkdir -p $tmp

    # Setting variables for the current option
    prep=$corpus/standard
    tmp=$prep/tmp
    mkdir -p $tmp

    echo 'Looking for Moses github repository (for tokenization scripts)...'
    DIR="$TOOLS/mosesdecoder"
    if [ -d "$DIR" ]; then
        echo "Moses repo was already cloned here."
    else
        echo 'Cloning Moses github repository.'
        git clone https://github.com/moses-smt/mosesdecoder.git $TOOLS/
    fi

    echo 'Looking for Subword NMT repository (for BPE pre-processing)...'
    DIR="$TOOLS/subword-nmt"
    if [ -d "$DIR" ]; then
        echo "Subword NMT repo was already cloned here."
    else
        echo 'Cloning Subword NMT repository.'
        git clone https://github.com/rsennrich/subword-nmt.git $TOOLS/
    fi

    if [ -d "$orig" ]; then
        echo "Retrieving dataset from $orig"
    else
        echo "Dataset is not available at $orig"
        exit 1
    fi

    # echo "Pre-processing data ..."
    # for t in "train" "test" "dev"; do
    #     for i in "input" "output"; do
    #         cat $orig/conll2012.$i.$t | \
    #         perl $TOKENIZER -threads 8 -$src > $tmp/$t.$i.tok.$src
    #     done
    # done

    echo "Pre-processing data ..."
    for t in "train" "test" "dev"; do
        for i in $src $tgt; do
            cp $orig/conll2012.$i.$t $tmp/$t.tok.$i
        done
    done
    for l in $src $tgt; do 
        mv $tmp/dev.tok.$l $tmp/valid.tok.$l
    done

    echo "Retrieving Heads ..."
    for t in "train" "test" "valid"; do
        for i in $src $tgt; do
            python $HEADS --regular-expression="<End-Of-Document>\n" $tmp/$t.tok.$i

            mv $tmp/$t.tok.$i $prep/$t.$i
            mv $tmp/$t.tok.$i.heads $prep/$t.$lang.$i.heads
        done
    done

    echo "Printing stats train stats..."
    for l in $src $tgt; do
        echo "Stats for train.$src (tokenized and cleaned):"
        words=$(wc -w $prep/train.$l | awk '{print $1;}')
        sents=$(wc -l $prep/train.$l | awk '{print $1;}')
        printf "%10d words \n" $words
        printf "%10d sentences \n" $sents
        printf "%10s wps \n" $(echo "scale=2 ; $words / $sents" | bc)
        echo
    done

    echo "Binarizing data ..."
    rm -rf data-bin/$prep
    fairseq-preprocess \
        --source-lang $src \
        --target-lang $tgt \
        --trainpref $prep/train \
        --testpref $prep/test \
        --validpref $prep/valid \
        --joined-dictionary \
        --destdir data-bin/$prep \
        --workers 8
    for t in "train" "test" "valid"; do
        for l in $src $tgt; do 
            cp $prep/$t.$lang.$l.heads data-bin/$prep/
        done
    done
        # --srcdict $HOME/dev/fairseq/data/models/roberta/roberta.large/dict.txt \
    #     --srcdict data-bin/$CODE_SOURCE_DIR/standard/dict.en.txt \



fi