from typing import List, Tuple

from transformers import AutoTokenizer, AutoModelForCausalLM

from .constants import MODEL_GENERATION


class GenerationExecutor:
    def __init__(self):
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_GENERATION,
            trust_remote_code=True,
            local_files_only=True,
        )

        model = AutoModelForCausalLM.from_pretrained(
            MODEL_GENERATION,
            device_map="cuda",
            trust_remote_code=True,
            local_files_only=True,
        ).eval()

        self.model = model
        self.tokenizer = tokenizer

    def chat(self, input_text: str, history: List[Tuple[str, str]] = None) -> str:
        response, _ = self.model.chat(self.tokenizer, input_text, history=history)
        return response
