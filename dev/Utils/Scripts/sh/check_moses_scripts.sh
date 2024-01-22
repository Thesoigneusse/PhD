#!/bin/bash

# Read script arguments and assign them to variables
for argument in "$@" 
do

    key=$(echo $argument | cut -f1 -d=)
    value=$(echo $argument | cut -f2 -d=)   
    if [[ $key == *"--"* ]]; then
        v="${key/--/}"
        declare $v="${value}" 
   fi
done

# Global variables
if [ -n "$SCRIPTS" ]; then SCRIPTS=$SCRIPTS; else SCRIPTS=$HOME/dev/Utils/Scripts ; fi
if [ -n "$this_script" ]; then this_script=$this_script; else this_script=$SCRIPTS/sh/check_moses_scripts.sh ; fi

# Fairseq variables
if [ -n "$FAIRSEQ" ]; then FAIRSEQ=$FAIRSEQ ; else FAIRSEQ=$HOME/dev/fairseq ;fi
if [ -n "$TOOLS_FAIRSEQ" ]; then TOOLS_FAIRSEQ=$TOOLS_FAIRSEQ ; else TOOLS_FAIRSEQ=$FAIRSEQ/tools ;fi
if [ -n "$SCRIPTS_FAIRSEQ" ]; then SCRIPTS_FAIRSEQ=$SCRIPTS_FAIRSEQ ; else SCRIPTS_FAIRSEQ=$TOOLS_FAIRSEQ/mosesdecoder/scripts ;fi
if [ -n "$NORM_PUNC" ]; then NORM_PUNC=$NORM_PUNC ; else NORM_PUNC=$SCRIPTS_FAIRSEQ/tokenizer/normalize-punctuation.perl ;fi
if [ -n "$CLEAN" ]; then CLEAN=$CLEAN ; else CLEAN=$$SCRIPTS_FAIRSEQ/training/clean-corpus-n.perl ;fi
if [ -n "$TOKENIZER_EN" ]; then TOKENIZER_EN=$TOKENIZER_EN ; else TOKENIZER_EN=$SCRIPTS_FAIRSEQ/tokenizer/tokenizer.perl ;fi
if [ -n "$TOKENIZER_ZH" ]; then TOKENIZER_ZH=$TOKENIZER_ZH ; else TOKENIZER_ZH=$SCRIPT/tokenizer_jieba/Jieba_parallel ;fi
if [ -n "$REM_NON_PRINT_CHAR" ]; then REM_NON_PRINT_CHAR=$REM_NON_PRINT_CHAR ; else REM_NON_PRINT_CHAR=$SCRIPTS_FAIRSEQ/tokenizer/remove-non-printing-char.perl ;fi

echo " "
echo ' + Looking for Moses github repository (for tokenization scripts)...'
DIR=$TOOLS_FAIRSEQ/mosesdecoder
if [ -d "$DIR" ]; then 
    echo " - Moses repo was already cloned here."
else
    cd $TOOLS_FAIRSEQ
    echo ' - Cloning Moses github repository.'
    git clone https://github.com/moses-smt/mosesdecoder.git
    cd -
fi

echo ' + Looking for Subword NMT repository (for BPE pre-processing)...'
DIR=$TOOLS_FAIRSEQ/subword-nmt
if [ -d "$DIR" ]; then
cd $TOOLS_FAIRSEQ
    echo " - Subword NMT repo was already cloned here."
else
    echo ' - Cloning Subword NMT repository.'
    git clone https://github.com/rsennrich/subword-nmt.git
    cd -
fi

if [ ! -d "$SCRIPTS_FAIRSEQ" ]; then
    echo " + Please set SCRIPTS variable correctly to point to Moses scripts."
    exit
fi
echo "... End"