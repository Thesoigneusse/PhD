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
if [ -n "$SCRIPT" ]; then SCRIPT=$SCRIPT; else SCRIPT=$HOME/dev/Utils/Scripts ; fi
if [ -n "$this_script" ]; then this_script=$this_script; else this_script=$SCRIPT/sh/zh-en/pre_process.sh ; fi

# Fairseq variables
if [ -n "$FAIRSEQ" ]; then FAIRSEQ=$FAIRSEQ ; else FAIRSEQ=$HOME/dev/fairseq ;fi
if [ -n "$TOOLS_FAIRSEQ" ]; then TOOLS_FAIRSEQ=$TOOLS_FAIRSEQ ; else TOOLS_FAIRSEQ=$FAIRSEQ/tools ;fi
if [ -n "$SCRIPT_FAIRSEQ" ]; then SCRIPT_FAIRSEQ=$SCRIPT_FAIRSEQ ; else SCRIPT_FAIRSEQ=$TOOLS_FAIRSEQ/mosesdecoder/scripts ;fi
if [ -n "$NORM_PUNC" ]; then NORM_PUNC=$NORM_PUNC ; else NORM_PUNC=$SCRIPT_FAIRSEQ/tokenizer/normalize-punctuation.perl ;fi
if [ -n "$CLEAN" ]; then CLEAN=$CLEAN ; else CLEAN=$$SCRIPT_FAIRSEQ/training/clean-corpus-n.perl ;fi
if [ -n "$TOKENIZER_EN" ]; then TOKENIZER_EN=$TOKENIZER_EN ; else TOKENIZER_EN=$SCRIPT_FAIRSEQ/tokenizer/tokenizer.perl ;fi
if [ -n "$TOKENIZER_ZH" ]; then TOKENIZER_ZH=$TOKENIZER_ZH ; else TOKENIZER_ZH=$SCRIPT/tokenizer_jieba/Jieba_parallel.py ;fi
if [ -n "$REM_NON_PRINT_CHAR" ]; then REM_NON_PRINT_CHAR=$REM_NON_PRINT_CHAR ; else REM_NON_PRINT_CHAR=$SCRIPT_FAIRSEQ/tokenizer/remove-non-printing-char.perl ;fi

# Script variables
if [ -n "$input_path" ]; then input_path=$input_path ; else input_path= ;fi
if [ -n "$input_file" ]; then input_file=$input_file ; else input_file= ;fi
if [ -n "$output_path" ]; then output_path=$output_path ; else output_path=$input_path/output ; fi
if [ -n "$output_file" ]; then output_file=$output_file ; else output_file=$input_file.tok ; fi
if [ -n "$only_en" ]; then only_en=$only_en ; else only_en=false ;fi
if [ -n "$only_zh" ]; then only_zh=$only_zh ; else only_zh=false ;fi

TMP=$output_path/.temp

# Create temp folder
mkdir -p $TMP

echo " "
echo "Pre-processing Data..."

echo " + Working on ..."
echo " - Input path: $input_path"
echo " - File: $input_file"
if $only_en; then echo " - Only EN language"; fi
if $only_zh; then echo " - Only ZH language"; fi

# Chinese Tokenisation
if ! $only_zh ; then
    echo " + Cleaning .zh file ..."
        cat $input_path/$input_file.zh | \
                perl $NORM_PUNC en | \
                perl $REM_NON_PRINT_CHAR > $TMP/tags.en-zh.clean.zh
    echo "   ... Cleaning .zh Done"

    echo " + Tokenize .zh file ..."
        python $TOKENIZER_ZH -i $TMP/tags.en-zh.clean.zh -o $TMP/tags.en-zh.tok.zh
    echo "   ... Tokenize .zh file Done"
fi

# English Tokenisation
if ! $only_en ; then
    echo " + Cleaning .en file ..."
    cat $input_path/$input_file.en | \
        perl $NORM_PUNC en | \
        perl $REM_NON_PRINT_CHAR > $TMP/tags.en-zh.clean.en
    echo "   ... Cleaning Done"

    echo " + Tokenize .en file ..."
    cat $TMP/tags.en-zh.clean.en | \
        perl $TOKENIZER_EN -threads 8 -a -l en > $TMP/tags.en-zh.tok.en
    echo "   ... Tokenize .en file Done"
fi

# Moving File
if ! $only_zh ; then
    echo " + Moving .zh file ..."
    echo " - From $TMP"
    echo " - To $output_path"
    mv $TMP/tags.en-zh.tok.zh $output_path/$output_file.zh
    echo "   ...Moving Done"
fi
if ! $only_en ; then
    echo " + Moving .en file ..."
    echo " - From $TMP"
    echo " - To $output_path"
    mv $TMP/tags.en-zh.tok.en $output_path/$output_file.en
    echo "   ...Moving Done"
fi

echo " + Cleaning process ..."
#rm -r $TMP
echo "   ... Cleaning Done"

echo "... Pre-processing Data Done"
echo " "