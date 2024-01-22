#!/bin/bash

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
if [ -n "$this_script" ]; then this_script=$this_script; else this_script=$SCRIPT_SPLITTING/$lang/nei/Pre-process.sh ; fi

# Script variable
if [ -n "$INPUT_PATH" ]; then INPUT_PATH=$INPUT_PATH ; else INPUT_PATH= ;fi
if [ -n "$input_file" ]; then input_file=$input_file ; else input_file= ;fi
if [ -n "$src" ]; then src=$src ; else src= ;fi
if [ -n "$tgt" ]; then tgt=$tgt ; else tgt= ;fi

lang=$src-$tgt
echo " "
echo "Printing stats train stats..."
echo " -> Working on ..."
echo " - INPUT_PATH: $INPUT_PATH"
echo " - input_file: $input_file"
for l in $src $tgt; do
    echo " -> Language: $l ..."
    echo " - Stats for $input_file.$l:"
    if [ "$l" = "zh" ]; then
        echo "Chinese not supported"
    else
        words=$(wc -w $INPUT_PATH/$input_file.$l | awk '{print $1;}')
        sents=$(wc -l $INPUT_PATH/$input_file.$l | awk '{print $1;}')
        printf " - Nombre de mots: %10d \n" $words
        printf " - Nombre de phrases: %10d \n" $sents
        printf " - wps: %10s \n" $(echo "scale=2 ; $words / $sents" | bc)
    fi
done
echo " "
