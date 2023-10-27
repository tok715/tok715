from typing import List, Tuple

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig

from .constants import MODEL_GENERATION

HistoryType = List[Tuple[str, str]]
TokensType = List[int]
BatchTokensType = List[List[int]]

im_start, im_end, endoftext = "<|im_start|>", "<|im_end|>", "<|endoftext|>"
role_system = "system"
role_user = "user"
role_assistant = "assistant"


class GenerationExecutor:
    def __init__(self):
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

        self.model = model
        self.tokenizer = tokenizer
        # common tokens
        self.tokens_im_start = tokenizer.encode(im_start)
        self.tokens_im_end = tokenizer.encode(im_end)
        self.tokens_nl = tokenizer.encode("\n")
        self.tokens_endoftext = tokenizer.encode(endoftext)
        self.tokens_system = tokenizer.encode(role_system)
        self.tokens_user = tokenizer.encode(role_user)
        self.tokens_assistant = tokenizer.encode(role_assistant)

    def encode_role(self, role: str):
        if role == role_system:
            return self.tokens_system
        elif role == role_user:
            return self.tokens_user
        elif role == role_assistant:
            return self.tokens_assistant
        else:
            return self.tokenizer.encode(role)

    def tokenize_line(self, role, content) -> Tuple[str, TokensType]:
        """
        tokenize a ChatML formatted line
        :param role: one of system, user, assistant
        :param content: the content of the line
        :return:
        """
        return (
            f"{im_start}{role}\n{content}{im_end}",
            self.tokens_im_start +
            self.encode_role(role) +
            self.tokens_nl +
            self.tokenizer.encode(content) +
            self.tokens_im_end,
        )

    def create_context_for_generation(self, existing: List[Tuple[str, str]]) -> Tuple[str, TokensType]:
        """
        create a context for generation from a list of existing lines
        :param existing:
        :return:
        """
        output_text = ""
        output_tokens = []
        for role, content in existing:
            text, tokens = self.tokenize_line(role, content)
            output_text += text
            output_text += "\n"
            output_tokens += tokens
            output_tokens += self.tokens_nl
        output_text += f'{im_start}{role_assistant}\n'
        output_tokens += self.tokens_im_start + self.tokens_assistant + self.tokens_nl
        return output_text, output_tokens

    def generate(self, existing: List[Tuple[str, str]]) -> str:
        text, tokens = self.create_context_for_generation(existing)

        outputs = self.model.generate(
            torch.tensor([tokens]).cuda(),
            # stop_words_ids = stop_words_ids,
            return_dict_in_generate=False,
        )[0]

        if torch.is_tensor(tokens):
            outputs = outputs.cpu().numpy().tolist()

        # remove context
        outputs = outputs[len(tokens):]

        # create output_text
        output_text = self.tokenizer.decode(outputs)

        for mark in [endoftext, im_start, im_start]:
            output_text = output_text.replace(mark, "").strip()

        return output_text
