from typing import List

from sentence_transformers import SentenceTransformer

MODEL_EMBEDDINGS = "intfloat/multilingual-e5-large"


class EmbeddingsExecutor:
    def __init__(self):
        self.st = SentenceTransformer(
            MODEL_EMBEDDINGS,
            device='cuda',
            cache_folder='_cache',
        )

    def encode(self, input_texts: List[str]) -> List[List[float]]:
        output = self.st.encode([
            "query: " + input_text for input_text in input_texts
        ], normalize_embeddings=True)
        return [
            t.tolist() for t in output
        ]
