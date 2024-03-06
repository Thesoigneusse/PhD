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

if [ -n "$help" ]; then help=$help ; else help=false ; fi
if $help ; then
    echo "HELP :"
    echo ""
    echo "* INPUT"
    echo "*   --input_path: path to the input file. Default: None"
    echo "*   --input_file: name of the input file. Default: None"
    echo ""
    echo "* OUTPUT"
    echo "*   --output_path: path to the output folder. Default: output_folder_name/output"
    echo "*   --output_headed_file: name of the output file (without the change of file white line). Default: input_file_name.headed"
    echo "*   --output_head_file: name of the output head file (where the beginning line of the document is writted). Default: input_file_name.heads"
    echo ""
    echo "* FEATURES"
    echo "*   --fill_size: maximal size of a document. Default: 1000"
    return 0
fi 
# Global variables
if [ -n "$SCRIPTS" ]; then SCRIPTS=$SCRIPTS; else SCRIPTS=$HOME/dev/Utils/Scripts ; fi
if [ -n "$this_script" ]; then this_script=$this_script; else this_script=$SCRIPTS/sh/retrieve_head.sh ; fi
if [ -n "$retrieve_head_script" ]; then retrieve_head_script=$retrieve_head_script; else retrieve_head_script=$SCRIPTS/python/retrieve_head.py ; fi

# Script variables
if [ -n "$input_path" ]; then input_path=$input_path ; else input_path= ; fi
if [ -n "$input_file" ]; then input_file=$input_file; else input_file= ; fi
if [ -n "$output_path" ]; then output_path=$output_path ; else output_path=$input_path/output ; fi
if [ -n "$output_headed_file" ]; then output_headed_file=$output_headed_file; else output_headed_file=$input_file.headed ; fi
if [ -n "$output_head_file" ]; then output_head_file=$output_head_file; else output_head_file=$input_file.heads ; fi
if [ -n "$fill_size" ]; then fill_size=$fill_size ; else fill_size=1000 ; fi



TMP=$output_path/.temp

echo " "
echo "Retriving Head..."

echo " + Working on ..."
echo " - Input path: $input_path..."
echo " - File: $input_file"
# Create temp folder
mkdir -p $TMP
mkdir -p $output_path

# Solve head retrival and put result on the temp folder
python $retrieve_head_script -c "standard" -i $input_path/$input_file -o $TMP/$input_file.headed -r $TMP/$input_file.heads
echo "   ... Working Done"

# Move result on output folder
echo " + Moving file ..."
echo " - From $TMP"
echo " - To $output_path"
mv $TMP/$input_file.headed $output_path/$output_headed_file
mv $TMP/$input_file.heads $output_path/$output_head_file
echo "   ...Moving Done"

# echo " + Cleaning process ..."
# rm -r $TMP
# echo "   ... Cleaning Done"

echo "... Retriving Head Ended"
echo " "