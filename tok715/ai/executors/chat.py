from typing import List, Tuple

from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer

MODEL_GENERATION = "train_output"


class ChatExecutor:
    def __init__(self):
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_GENERATION,
            trust_remote_code=True,
            local_files_only=True,
        )

        model = AutoPeftModelForCausalLM.from_pretrained(
            MODEL_GENERATION,
            device_map="cuda",
            trust_remote_code=True,
            local_files_only=True,
        ).eval()

        self.model = model
        self.tokenizer = tokenizer

    def chat(self, **kwargs) -> Tuple[str, List[List[str]]]:
        return self.model.chat(self.tokenizer, **kwargs)
