#!/bin/bash

set -eu

cd "$(dirname "${0}")"

MODEL="Qwen/Qwen-7B-Chat-Int4"

DIR_QWEN="../3rdparty/qwen"
DIR_DATA="../data"

PATH_TRAIN_DATA="${DIR_DATA}/train_data.json"
PATH_TRAIN_OUTPUT="${DIR_DATA}/train_output"

python3 prepare.py --input data.txt --output "${PATH_TRAIN_DATA}"

export CUDA_DEVICE_MAX_CONNECTIONS=1
export CUDA_VISIBLE_DEVICES=0

# Remember to use --fp16 instead of --bf16 due to autogptq
python "${DIR_QWEN}/finetune.py" \
  --model_name_or_path "${DIR_DATA}/${MODEL}" \
  --data_path "${PATH_TRAIN_DATA}" \
  --fp16 True \
  --output_dir "${PATH_TRAIN_OUTPUT}" \
  --num_train_epochs 5 \
  --per_device_train_batch_size 2 \
  --per_device_eval_batch_size 1 \
  --gradient_accumulation_steps 8 \
  --evaluation_strategy "no" \
  --save_strategy "steps" \
  --save_steps 1000 \
  --save_total_limit 10 \
  --learning_rate 3e-4 \
  --weight_decay 0.1 \
  --adam_beta2 0.95 \
  --warmup_ratio 0.01 \
  --lr_scheduler_type "cosine" \
  --logging_steps 1 \
  --report_to "none" \
  --model_max_length 512 \
  --lazy_preprocess True \
  --gradient_checkpointing \
  --use_lora \
  --q_lora \
  --deepspeed "${DIR_QWEN}/finetune/ds_config_zero2.json"
