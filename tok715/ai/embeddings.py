from typing import List

from sentence_transformers import SentenceTransformer


def ai_embeddings_create(transformer: SentenceTransformer, input_texts: List[str]) -> List[List[float]]:
    output = transformer.encode([
        "query: " + input_text for input_text in input_texts
    ], normalize_embeddings=True)
    return [
        t.tolist() for t in output
    ]
