import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig, AutoModel

from tok715.constants import MODEL_GENERATION, MODEL_EMBEDDINGS


def load_embeddings_model_tokenizer():
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_EMBEDDINGS,
        trust_remote_code=True,
        local_files_only=True,
    )
    model = AutoModel.from_pretrained(
        MODEL_EMBEDDINGS,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        local_files_only=True,
    ).eval()
    return model, tokenizer


def load_generation_model_tokenizer():
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_GENERATION,
        trust_remote_code=True,
        local_files_only=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_GENERATION,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        local_files_only=True,
    ).eval()
    model.generation_config = GenerationConfig.from_pretrained(
        MODEL_GENERATION,
        trust_remote_code=True,
        local_files_only=True,
    )
    model.generation_config.do_sample = False  # use greedy decoding

    return model, tokenizer
