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
if [ -n "$this_script" ]; then this_script=$this_script; else this_script=$SCRIPT/sh/en-de/pre_process.sh ; fi
if [ -n "$src" ]; then src=$src; else src=en ; fi
if [ -n "$tgt" ]; then tgt=$tgt; else tgt=de ; fi
lang=$src-$tgt


# Fairseq variables
if [ -n "$FAIRSEQ" ]; then FAIRSEQ=$FAIRSEQ ; else FAIRSEQ=$HOME/dev/fairseq ;fi
if [ -n "$TOOLS_FAIRSEQ" ]; then TOOLS_FAIRSEQ=$TOOLS_FAIRSEQ ; else TOOLS_FAIRSEQ=$FAIRSEQ/tools ;fi
if [ -n "$SCRIPT_FAIRSEQ" ]; then SCRIPT_FAIRSEQ=$SCRIPT_FAIRSEQ ; else SCRIPT_FAIRSEQ=$TOOLS_FAIRSEQ/mosesdecoder/scripts ;fi
if [ -n "$NORM_PUNC" ]; then NORM_PUNC=$NORM_PUNC ; else NORM_PUNC=$SCRIPT_FAIRSEQ/tokenizer/normalize-punctuation.perl ;fi
if [ -n "$CLEAN" ]; then CLEAN=$CLEAN ; else CLEAN=$$SCRIPT_FAIRSEQ/training/clean-corpus-n.perl ;fi
if [ -n "$TOKENIZER_EN" ]; then TOKENIZER_EN=$TOKENIZER_EN ; else TOKENIZER_EN=$SCRIPT_FAIRSEQ/tokenizer/tokenizer.perl ;fi
if [ -n "$TOKENIZER_DE" ]; then TOKENIZER_DE=$TOKENIZER_DE ; else TOKENIZER_DE=$SCRIPT_FAIRSEQ/tokenizer/tokenizer.perl ;fi
if [ -n "$REM_NON_PRINT_CHAR" ]; then REM_NON_PRINT_CHAR=$REM_NON_PRINT_CHAR ; else REM_NON_PRINT_CHAR=$SCRIPT_FAIRSEQ/tokenizer/remove-non-printing-char.perl ;fi

# Script variables
if [ -n "$input_path" ]; then input_path=$input_path ; else input_path= ;fi
if [ -n "$input_file" ]; then input_file=$input_file ; else input_file= ;fi
if [ -n "$output_path" ]; then output_path=$output_path ; else output_path=$input_path/output ; fi
if [ -n "$output_file" ]; then output_file=$output_file ; else output_file=$input_file.tok ; fi
if [ -n "$only_en" ]; then only_en=$only_en ; else only_en=false ;fi
if [ -n "$only_de" ]; then only_de=$only_de ; else only_de=false ;fi

TMP=$output_path/.temp

# Create temp folder
mkdir -p $TMP

echo " "
echo "Pre-processing Data..."

echo " + Working on ..."
echo " - Input path: $input_path"
echo " - File: $input_file"
if $only_en; then echo " - Only EN language"; fi
if $only_de; then echo " - Only DE language"; fi

# German Tokenisation
if ! $only_en ; then
    echo " + Cleaning .$tgt file ..."
        cat $input_path/$input_file.$tgt | \
            perl $NORM_PUNC $tgt | \
            perl $REM_NON_PRINT_CHAR > $TMP/tags.$lang.clean.$tgt
    echo "   ... Cleaning .$tgt Done"

    echo " + Tokenize .$tgt file ..."
    cat $TMP/tags.$lang.clean.$tgt | \
        perl $TOKENIZER_DE -threads 8 -a -l $tgt > $TMP/tags.$lang.tok.$tgt
    echo "   ... Tokenize .$tgt file Done"
fi

# English Tokenisation
if ! $only_de ; then
    echo " + Cleaning .$src file ..."
    cat $input_path/$input_file.$src | \
        perl $NORM_PUNC $src | \
        perl $REM_NON_PRINT_CHAR > $TMP/tags.$lang.clean.$src
    echo "   ... Cleaning $src Done"

    echo " + Tokenize .$src file ..."
    cat $TMP/tags.$lang.clean.$src | \
        perl $TOKENIZER_EN -threads 8 -a -l $src > $TMP/tags.$lang.tok.$src
    echo "   ... Tokenize .$src file Done"
fi

# Moving File
if ! $only_de ; then
    echo " + Moving .$tgt file ..."
    echo " - From $TMP"
    echo " - To $output_path"
    mv $TMP/tags.$lang.tok.$tgt $output_path/$output_file.$tgt
    echo "   ...Moving Done"
fi
if ! $only_en ; then
    echo " + Moving .$src file ..."
    echo " - From $TMP"
    echo " - To $output_path"
    mv $TMP/tags.$lang.tok.$src $output_path/$output_file.$src
    echo "   ...Moving Done"
fi

echo " + Cleaning process ..."
#rm -r $TMP
echo "   ... Cleaning Done"

echo "... Pre-processing Data Done"
echo " "