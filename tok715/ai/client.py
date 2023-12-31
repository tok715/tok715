from typing import Dict, List

import requests


class AIServiceClient:
    def __init__(self, conf: Dict):
        self.url = conf['ai_service']['url']

    def _invoke(self, method: str, args: Dict) -> Dict:
        r = requests.post(self.url, json={'method': method, 'args': args})
        if r.status_code != 200:
            raise Exception('failed invoking ai_service: ' + r.text)
        data = r.json()
        return data['result']

    def invoke_embeddings(self, input_texts: List[str]) -> List[List[float]]:
        args = {'input_texts': input_texts}
        result = self._invoke('embeddings', args)
        return result['vectors']

    def invoke_chat(self, query: str, history: List[List[str]] = None, system: str = None) -> str:
        if history is None:
            history = []
        result = self._invoke('chat', {
            'query': query,
            'history': history,
            'system': system,
        })
        return result['response']


def create_ai_service_client(conf: Dict) -> AIServiceClient:
    return AIServiceClient(conf)
