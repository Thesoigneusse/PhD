#!/bin/bash

#SBATCH --job-name=
#SBATCH --time=15:00:00
#SBATCH --nodes=1
#SBATCH --gres=gpu:4
#SBATCH -C v100-32g
#SBATCH --output=/linkhome/rech/genlig01/ujv46tt/.local/outputs/%j.out
#SBATCH --error=/linkhome/rech/genlig01/ujv46tt/.local/outputs/%j.err
#SBATCH --account=qda@v100
#SBATCH --qos=qos_gpu-t3
#SBATCH --mail-type=ALL
#SBATCH --mail-user=fabien.lopez@univ-grenoble-alpes.fr
#SBATCH --hint=nomultithread
#SBATCH --cpus-per-task=24


# Activate data collection about GPU energy consumption
#/usr/local/bin/dcgmi-slurm-start.sh

# nettoyage des modules charges en interactif et herites par defaut
#module purge
 
# chargement des modules
# module load ...

# echo des commandes lancées
#set -x


#export PYTHONIOENCODING=UTF-8
#export LC_ALL=C.UTF-8
#export LANG=C.UTF-8

#HOME=/linkhome/rech/genlig01/ujv46tt/.local
HOME=/home/getalp/lopezfab/PhD
LORENZO_CODE=$HOME/dev/fairseq
DATA=$HOME/dev/fairseq/data/coreference


echo " "
echo "Lancement de l'environnement..."

# conda activate PhD
# echo $PATH
echo "Environnement lancé"

echo " "
echo "Execution de la commande..."


bash $LORENZO_CODE/sh/run/coreference/conll-2012/concat.sh --t=train \
    --data_dir=$DATA/data-bin/conll-2012/standard \
    --save_dir=$HOME/checkpoints/coreference/test_seq2seq \
    --arch="concat_vaswani_wmt_en_fr_new_attn" \
    --lr=5e-4 \
    --scored_checkpoint="avg_closest" \
    --ncheckpoints=5 \
    --dropout=0.3 \
    --patience=2 \
    --max_tokens=200 --update_freq=1  \
    --kind_attention_head="multihead_attention" \
    --fp16 \
    --mode=slide_n2n --opt=num-sent --val=4 --need_seg_label=True
    # --roberta_model="$HOME/dev/fairseq/data/models/roberta/roberta.large/model.pt" \
    # --share_all_embeddings=False \
# --pretrained="$HOME/checkpoints/en-de/baseline_transformer_en_fr.en-de.SL" \

# bash $LORENZO_CODE/sh/slurm/en-de/temp_naver-submit-transfo.slurm

# bash $LORENZO_CODE/sh/run/zh-en/2023LiteraryTranslationChallenge/transfo_base.sh \
#     --data_dir=$DATA/2023LiteraryTranslationChallenge/pre-train_test2_valid2/ \
#     --save_dir=$DATA/2023LiteraryTranslationChallenge/pre-train_test2_valid2/ \
#     --t=average \
#     --mode=slide_n2n --opt=num-sent --val=4

# bash $LORENZO_CODE/sh/run/en-de/iwslt17/concat.sh --t=finetune \
#     --src=zh \
#     --tgt=en \
#     --task="doc2doc_translation" \
#     --arch="concat_vaswani_wmt_zh_en" \
#     --data-dir=$DATA/2023LiteraryTranslationChallenge/train_test2_valid2 \
#     --save-dir=$HOME/checkpoints/zh-en/DL.4to4.cd0.01/ \
#     --max-tokens=8000 --update-freq=1 \
#     --patience=12 \
#     --mode=slide_n2n --opt=num-sent --val=4 \
#     --context_discount=0.01 \
#     --pretrained=$HOME/checkpoints/zh-en/SL-transformer.zh-en/Average_closest/checkpoint.avg_closest5.pt
    
echo "commande executee"

#/usr/local/bin/dcgmi-slurm-stop.sh


