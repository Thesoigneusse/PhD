#!/bin/bash

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
if [ -n "$this_script" ]; then this_script=$this_script; else this_script=$SCRIPT_SPLITTING/$lang/nei/Pre-process.sh ; fi

# Fairseq variables
if [ -n "$FAIRSEQ" ]; then FAIRSEQ=$FAIRSEQ ; else FAIRSEQ=$HOME/dev/fairseq ;fi
if [ -n "$TOOLS_FAIRSEQ" ]; then TOOLS_FAIRSEQ=$TOOLS_FAIRSEQ ; else TOOLS_FAIRSEQ=$FAIRSEQ/tools ;fi
if [ -n "$SCRIPT_FAIRSEQ" ]; then SCRIPT_FAIRSEQ=$SCRIPT_FAIRSEQ ; else SCRIPT_FAIRSEQ=$TOOLS_FAIRSEQ/mosesdecoder/scripts ;fi
if [ -n "$TOKENIZER" ]; then TOKENIZER=$TOKENIZER ; else TOKENIZER=$SCRIPT_FAIRSEQ/tokenizer/tokenizer.perl ;fi
# Script of Lorenzo
if [ -n "$SCRIPT_LORENZO" ]; then SCRIPT_LORENZO=$SCRIPT_LORENZO ; else SCRIPT_LORENZO=$HOME/lorenzo_code/focused-concat; fi
if [ -n "$CLEAN" ]; then CLEAN=$CLEAN; else CLEAN=$SCRIPT_LORENZO/scripts/clean-corpus-n-leaving-blanks.perl; fi
# Script of Fabien
if [ -n "$FAB_SCRIPT" ]; then FAB_SCRIPT=$FAB_SCRIPT ; else FAB_SCRIPT=$HOME/dev/Utils/Scripts
if [ -n "$PRINT_STAT" ]; then PRINT_STAT=$PRINT_STAT; else PRINT_STAT=$FAB_SCRIPT/sh/print_stat.sh; fi
if [ -n "$RETRIEVE_HEAD" ]; then RETRIEVE_HEAD=$RETRIEVE_HEAD; else RETRIEVE_HEAD=$FAB_SCRIPT/sh/retrieve_head.sh; fi



# Script variables
if [ -n "$INPUT_PATH" ]; then INPUT_PATH=$INPUT_PATH ; else INPUT_PATH= ;fi
if [ -n "$OUTPUT_PATH" ]; then OUTPUT_PATH=$OUTPUT_PATH ; else OUTPUT_PATH=$INPUT_PATH/output ; fi


if [ -n "$src" ]; then src=$src ; else src= ;fi
if [ -n "$tgt" ]; then tgt=$tgt ; else tgt= ;fi


TMP=$OUTPUT_PATH/.temp
mkdir -p $TMP

echo " "
echo "Applying standart split on NEI ..."
echo " + Working on ..."
echo " - Script file: $this_script"
echo " - Input path: $input_path"

# Checking Moses scripts
if $bool_check_moses;then
    bash $check_moses_scripts
fi

# Pre-processing data
echo " "
echo "Pre-processing train data..."
for l in $src $tgt; do
    # Select training files
    f=train.tags.$lang.$l
    tok=train.tags.$lang.tok.$l
    # Remove lines containing url, talkid and keywords (grep -v).
    # Remove special tokens with sed -e.
    # Then tokenize (insert spaces between words and punctuation) with moses.
    cat $TMP/$f | \
    grep -v '<doc ' | \
    grep -v '</doc>' | \
    grep -v '<url>' | \
    grep -v '</translator>' | \
    grep -v '</reviewer>' | \
    grep -v '</speaker>' | \
    grep -v '</keywords>' | \
    sed -e 's/<talkid>.*<\/talkid>//g' | \
    sed -e 's/<title>//g' | \
    sed -e 's/<\/title>//g' | \
    sed -e 's/<description>//g' | \
    sed -e 's/<\/description>//g' | \
    perl $TOKENIZER -threads 8 -l $l > $TMP/$tok
    echo ""
done
echo "...Pre-processing train data DONE"


  # Clean training files from long sentences (100 sentences longer then 175 tok),
  # [not empty sentences] and sentences that highly mismatch in length (ratio)
  perl $CLEAN -ratio 1.5 $TMP/train.tags.$lang.tok $src $tgt $TMP/train.tags.$lang 0 175

  echo "Pre-processing valid/test data..."
  for l in $src $tgt; do
      for o in `ls $TMP/IWSLT17.TED.*.$lang.$l.xml`; do
      fname=${o##*/}
        echo " + Working on ..."
        echo " - langue: $l"
        echo " - File Path/File: $o"
        echo " - File: $fname"
        cat $TMP/$fname | \
        sed '/<doc \s*/i <seg id="0">' | \
        grep '<seg id' | \
        sed -e 's/<seg id="[0-9]*">\s*//g' | \
        sed -e 's/\s*<\/seg>\s*//g' | \
        sed -e "s/\’/\'/g" | \
        perl $TOKENIZER -threads 8 -l $l > $TMP/$fname
        echo "...Done"
      done
  done
  echo "... Pre-processing valid/test data DONE"
  echo " "


echo "Creating train, valid, test data..."
    echo " + Working on ..."
    echo " - Path: $TMP"
    echo " - Files: train.tags.$lang"
    echo "          IWSLT17.TED.tst2011.$lang"
    echo "          IWSLT17.TED.tst2012.$lang"
    echo "          IWSLT17.TED.tst2013.$lang"
    echo "          IWSLT17.TED.tst2014.$lang"
    echo "          IWSLT17.TED.tst2015.$lang"
    for l in $src $tgt; do
        echo " - Language: $l"
        # textual datasets
        cat $TMP/train.tags.$lang.$l          > $TMP/train.$l
        cat $TMP/IWSLT17.TED.tst2011.$lang.$l \
            $TMP/IWSLT17.TED.tst2012.$lang.$l \
            $TMP/IWSLT17.TED.tst2013.$lang.$l \
            $TMP/IWSLT17.TED.tst2014.$lang.$l > $TMP/valid.$l  
        cat $TMP/IWSLT17.TED.tst2015.$lang.$l > $TMP/test.$l
        # retrieve indices of headlines
        python $RETRIEVE_HEAD --input-path="$TMP" \
                              --input_file="train.$l" \
                              --output_path="$TMP" \
                              --output_head_file="train.heads" \
                              --output_headed_file="train.headed"

        python $RETRIEVE_HEAD --input-path="$TMP" \
                              --input_file="valid.$l" \
                              --output_path="$TMP" \
                              --output_head_file="valid.$lang.$l.heads" \
                              --output_headed_file="valid.$lang.$l.headed"
        
        python $RETRIEVE_HEAD --input-path="$TMP" \
                              --input_file="test.$l" \
                              --output_path="$TMP" \
                              --output_head_file="test.$lang.$l.heads" \
                              --output_headed_file="test.$lang.$l.headed"

    done
echo "... Creating train, valid, test data DONE"

# Move result on output folder
echo " + Moving file ..."
echo " - From $TMP"
echo " - To $OUTPUT_PATH"
echo "   File: train"
for l in $src $tgt; do
    mv $TMP/train.headed $OUTPUT_PATH/train.$lang.$l.heads
    mv $TMP/train.heads $OUTPUT_PATH/train.$lang.$l.headed
done
echo " - Moving train Done"

echo " + Moving file ..."
echo "   From $TMP"
echo "   To $OUTPUT_PATH"
echo "   File: valid"
for l in $src $tgt; do
    mv $TMP/valid.headed $OUTPUT_PATH/valid.$lang.$l.heads
    mv $TMP/valid.heads $OUTPUT_PATH/valid.$lang.$l.headed
done
echo " - Moving valid Done"

echo " + Moving file ..."
echo "   From $TMP"
echo "   To $OUTPUT_PATH"
echo "   File: test"
for l in $src $tgt; do
    mv $TMP/test.headed $OUTPUT_PATH/test.$lang.$l.heads
    mv $TMP/test.heads $OUTPUT_PATH/test.$lang.$l.headed
done
echo " - Moving test Done"
echo "   ...Moving DONE"




