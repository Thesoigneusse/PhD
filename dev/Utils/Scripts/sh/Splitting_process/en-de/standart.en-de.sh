#!/bin/bash

bool_check_moses=false

src=en
tgt=de
lang=$src-$tgt


# Read script arguments and assign them to variables
for argument in "$@"; do

    key=$(echo $argument | cut -f1 -d=)
    value=$(echo $argument | cut -f2 -d=)   
    if [[ $key == *"--"* ]]; then
        v="${key/--/}"
        declare $v="${value}" 
   fi
done

# Global Variable
if [ -n "$SCRIPT" ]; then SCRIPT=$SCRIPT; else SCRIPT=$HOME/dev/Utils/Scripts ; fi
if [ -n "$SCRIPT_SPLITTING" ]; then SCRIPT_SPLITTING=$SCRIPT_SPLITTING; else SCRIPT_SPLITTING=$SCRIPT/sh/Splitting_process ; fi
if [ -n "$this_script" ]; then this_script=$this_script; else this_script=$SCRIPT_SPLITTING/$lang/standart.sh ; fi

# Fairseq variables
if [ -n "$FAIRSEQ" ]; then FAIRSEQ=$FAIRSEQ ; else FAIRSEQ=$HOME/dev/fairseq ;fi
if [ -n "$TOOLS_FAIRSEQ" ]; then TOOLS_FAIRSEQ=$TOOLS_FAIRSEQ ; else TOOLS_FAIRSEQ=$FAIRSEQ/tools ;fi
if [ -n "$SCRIPT_FAIRSEQ" ]; then SCRIPT_FAIRSEQ=$SCRIPT_FAIRSEQ ; else SCRIPT_FAIRSEQ=$TOOLS_FAIRSEQ/mosesdecoder/scripts ;fi
if [ -n "$CODE_SOURCE_DIR" ]; then CODE_SOURCE_DIR=$CODE_SOURCE_DIR ; else CODE_SOURCE_DIR= ;fi
if [ -n "$BPE_CODE" ]; then BPE_CODE=$BPE_CODE ; else BPE_CODE=$CODE_SOURCE_DIR/code ;fi
if [ -n "$BPEROOT" ]; then BPEROOT=$BPEROOT ; else BPEROOT=$TOOLS_FAIRSEQ/subword-nmt/subword_nmt ;fi


if [ -n "$FAB_SCRIPT" ]; then FAB_SCRIPT=$FAB_SCRIPT; ELSE $FAB_SCRIPT=$HOME/dev/Utils/Scripts
if [ -n "$SCRIPT_SPLITTING" ]; then SCRIPT_SPLITTING=$SCRIPT_SPLITTING; else SCRIPT_SPLITTING=$FAB_SCRIPT/sh/Splitting_process ; fi
if [ -n "$CHECK_MOSES_SCRIPTS" ]; then CHECK_MOSES_SCRIPTS=$CHECK_MOSES_SCRIPTS ; else CHECK_MOSES_SCRIPTS=$FAB_SCRIPT/sh/check_moses_scripts.sh ;fi
if [ -n "$PRE_PROCESS_SCRIPT" ]; then PRE_PROCESS_SCRIPT=$PRE_PROCESS_SCRIPT ; else PRE_PROCESS_SCRIPT=$SCRIPT_SPLITTING/$lang/nei/Pre-process.sh;fi


# Script variables
if [ -n "$INPUT_PATH" ]; then INPUT_PATH=$INPUT_PATH ; else INPUT_PATH= ;fi
if [ -n "$input_file" ]; then input_file=$input_file ; else input_file= ;fi
if [ -n "$OUTPUT_PATH" ]; then OUTPUT_PATH=$OUTPUT_PATH ; else OUTPUT_PATH=$INPUT_PATH/output ; fi
if [ -n "$output_file" ]; then output_file=$output_file ; else output_file=$input_file.tok ; fi

if [ -n "$src" ]; then src=$src ; else src= ;fi
if [ -n "$tgt" ]; then tgt=$tgt ; else tgt= ;fi


TMP=$OUTPUT_PATH/.temp
mkdir -p $TMP

echo " "
echo "Applying standart split ..."
echo " + Working on ..."
echo "   Script file: $this_script"
echo "   Input path: $INPUT_PATH"
echo "   Input file: $input_file"

# Checking Moses scripts
if $bool_check_moses;then
    bash $check_moses_scripts
fi

# Pre-processing data
echo "Pre-processing data..."
bash $PRE_PROCESS_SCRIPT --INPUT_PATH="$INPUT_PATH" \
                         --src="en" \
                         --tgt="de" \
                         --OUTPUT_PATH="$TMP" \


echo "... Pre-processing DONE"

echo "Applying BPEs..."
for l in $src $tgt; do
    for f in train.$l valid.$l test.$l; do
        echo " + Working on ..."
        echo "   Path: $TMP"
        echo "   File: $f"
        echo "   BPE_CODE: $BPE_CODE" 
        python $BPEROOT/apply_bpe.py -c $BPE_CODE < $TMP/$f > $TMP/$f
    done
done



fairseq-preprocess \
    --source-lang $src \
    --target-lang $tgt \
    --trainpref $OUTPUT_PATH/train \
    --validpref $OUTPUT_PATH/valid \
    --testpref $OUTPUT_PATH/test \
    --srcdict $CODE_SOURCE_DIR/standard/dict.en.txt \
    --joined-dictionary \
    --destdir $OUTPUT_PATH \
    --workers $N_THREADS
