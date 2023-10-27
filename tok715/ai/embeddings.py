from typing import List

from sentence_transformers import SentenceTransformer


class EmbeddingsExecutor:
    def __init__(self, st: SentenceTransformer):
        self.st = st

    def vectorize(self, input_texts: List[str]) -> List[List[float]]:
        output = self.st.encode([
            "query: " + input_text for input_text in input_texts
        ], normalize_embeddings=True)
        return [
            t.tolist() for t in output
        ]
