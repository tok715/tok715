from typing import List, Tuple, Optional, Union

import torch
from transformers import PreTrainedTokenizer

HistoryType = List[Tuple[str, str]]
TokensType = List[int]
BatchTokensType = List[List[int]]

im_start, im_end = "<|im_start|>", "<|im_end|>"


def make_context(
        tokenizer: PreTrainedTokenizer,
        query: str,
        history: List[Tuple[str, str]] = None,
        system: str = "",
        max_window_size: int = 6144,
        chat_format: str = "chatml",
        im_start_tokens=None,
        im_end_tokens=None,
        nl_tokens=None,
):
    if history is None:
        history = []

    def _tokenize_str(role, content):
        return f"{role}\n{content}", tokenizer.encode(
            role
        ) + nl_tokens + tokenizer.encode(content)

    system_text, system_tokens_part = _tokenize_str("system", system)
    system_tokens = im_start_tokens + system_tokens_part + im_end_tokens

    raw_text = ""
    context_tokens = []

    for turn_query, turn_response in reversed(history):
        query_text, query_tokens_part = _tokenize_str("user", turn_query)
        query_tokens = im_start_tokens + query_tokens_part + im_end_tokens
        response_text, response_tokens_part = _tokenize_str(
            "assistant", turn_response
        )
        response_tokens = im_start_tokens + response_tokens_part + im_end_tokens

        next_context_tokens = nl_tokens + query_tokens + nl_tokens + response_tokens
        prev_chat = (
            f"\n{im_start}{query_text}{im_end}\n{im_start}{response_text}{im_end}"
        )

        current_context_size = (
                len(system_tokens) + len(next_context_tokens) + len(context_tokens)
        )
        if current_context_size < max_window_size:
            context_tokens = next_context_tokens + context_tokens
            raw_text = prev_chat + raw_text
        else:
            break

    context_tokens = system_tokens + context_tokens
    raw_text = f"{im_start}{system_text}{im_end}" + raw_text
    context_tokens += (
            nl_tokens
            + im_start_tokens
            + _tokenize_str("user", query)[1]
            + im_end_tokens
            + nl_tokens
            + im_start_tokens
            + tokenizer.encode("assistant")
            + nl_tokens
    )
    raw_text += f"\n{im_start}user\n{query}{im_end}\n{im_start}assistant\n"

    return raw_text, context_tokens


def chat(
        model,
        tokenizer: PreTrainedTokenizer,
        query: str,
        history: Optional[HistoryType],
        system: str = "You are a helpful assistant.",
        append_history: bool = True
) -> Tuple[str, HistoryType]:
    # common tokens
    im_start_tokens = tokenizer.encode(im_start)
    im_end_tokens = tokenizer.encode(im_end)
    nl_tokens = tokenizer.encode("\n")

    if history is None:
        history = []

    raw_text, context_tokens = make_context(
        tokenizer,
        query,
        history=history,
        system=system,
        max_window_size=6144,
        chat_format="chatml",
        im_start_tokens=im_start_tokens,
        im_end_tokens=im_end_tokens,
        nl_tokens=nl_tokens
    )

    stop_words_ids = [im_end_tokens, im_end_tokens]
    input_ids = torch.tensor([context_tokens]).cuda()
    outputs = model.generate(
        input_ids,
        # stop_words_ids = stop_words_ids,
        return_dict_in_generate=False,
    )

    response = decode_tokens(
        outputs[0],
        tokenizer,
        raw_text_len=len(raw_text),
        context_length=len(context_tokens),
        chat_format='chatml',
        verbose=False,
        im_start_tokens=im_start_tokens,
        im_end_tokens=im_end_tokens,
    )

    if append_history:
        history.append((query, response))

    return response, history


def decode_tokens(
        tokens: Union[torch.LongTensor, TokensType],
        tokenizer: PreTrainedTokenizer,
        raw_text_len: int,
        context_length: int,
        chat_format: str = "chatml",
        verbose: bool = False,
        return_end_reason: bool = False,
        im_start_tokens=None,
        im_end_tokens=None,
) -> str:
    if torch.is_tensor(tokens):
        tokens = tokens.cpu().numpy().tolist()

    return _decode_chatml(
        tokens,
        stop_words=[],
        eod_token_ids=im_start_tokens + im_end_tokens,
        tokenizer=tokenizer,
        raw_text_len=raw_text_len,
        context_length=context_length,
        verbose=verbose,
        return_end_reason=return_end_reason,
    )


def _decode_chatml(
        tokens: List[int],
        *,
        stop_words: List[str],
        eod_token_ids: List[int],
        tokenizer: PreTrainedTokenizer,
        raw_text_len: int,
        context_length: int,
        verbose: bool = False,
        return_end_reason: bool = False,
        chat_format="chatml",
):
    end_reason = f"Gen length {len(tokens)}"
    eod_token_idx = context_length
    for eod_token_idx in range(context_length, len(tokens)):
        if tokens[eod_token_idx] in eod_token_ids:
            end_reason = f"Gen {tokenizer.decode([tokens[eod_token_idx]])!r}"
            break

    trim_decode_tokens = tokenizer.decode(tokens[:eod_token_idx])[raw_text_len:]
    if verbose:
        print("\nRaw Generate w/o EOD:", tokenizer.decode(tokens)[raw_text_len:])
        print("\nRaw Generate:", trim_decode_tokens)
        print("\nEnd Reason:", end_reason)
    for stop_word in stop_words:
        trim_decode_tokens = trim_decode_tokens.replace(stop_word, "").strip()
    trim_decode_tokens = trim_decode_tokens.strip()
    if verbose:
        print("\nGenerate:", trim_decode_tokens)

    if return_end_reason:
        return trim_decode_tokens, end_reason
    else:
        return trim_decode_tokens
