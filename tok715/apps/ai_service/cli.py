import http.server
import json
from typing import Dict

import click

from tok715.ai.embeddings import ai_embeddings_create
from tok715.ai.model import load_embeddings_sentence_transformer
from tok715.misc.config import load_config


class JSONInvokeHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):

    def read_json(self):
        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length)
        return json.loads(body)

    def send_json(self, data, code=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.send_json({"hello": "world"})

    def do_POST(self):
        try:
            data: Dict = self.read_json()
            data.update({
                'result': self.do_invoke(data['method'], data['args'])
            })
            self.send_json(data)
        except Exception as e:
            self.send_json({"error": str(e)}, code=500)

    def do_invoke(self, method: str, args: Dict) -> Dict:
        return {}


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
def main(opt_conf):
    conf = load_config(opt_conf)

    server_conf = conf["ai_service"]["server"]

    print("loading embeddings sentence transformer")
    e_transformer = load_embeddings_sentence_transformer()

    print("loading generation model")
    # g_model, g_tokenizer = load_generation_model_tokenizer()

    print("all models loaded")

    class AIServiceHTTPRequestHandler(JSONInvokeHTTPRequestHandler):

        def do_invoke(self, method: str, args: Dict) -> Dict:
            if method == "embeddings":
                return {
                    "vectors": ai_embeddings_create(e_transformer, args["input_texts"]),
                    "vector_version": server_conf["vector_version"]
                }
            return {}

    s = http.server.HTTPServer(
        (server_conf['host'], server_conf['port']),
        AIServiceHTTPRequestHandler,
    )
    s.serve_forever()


if __name__ == "__main__":
    main()
