import http.server
import json
from typing import Dict

import click

from tok715.ai.executors import EmbeddingsExecutor, GenerationExecutor
from tok715.misc import load_config


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
            self.send_json({
                'result': self.do_invoke(data['method'], data['args'])
            })
        except Exception as e:
            self.send_json({"error": str(e)}, code=500)

    def do_invoke(self, method: str, args: Dict) -> Dict:
        return {}


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
def main(opt_conf):
    conf = load_config(opt_conf)

    server_conf = conf["ai_service"]["server"]

    print("loading embeddings executor")
    e_executor = EmbeddingsExecutor()

    print("loading generation executor")
    g_executor = GenerationExecutor()

    print("all executors loaded")

    class AIServiceHTTPRequestHandler(JSONInvokeHTTPRequestHandler):

        def do_invoke(self, method: str, args: Dict) -> Dict:
            if method == "embeddings":
                return {
                    "vectors": e_executor.vectorize(args["input_texts"]),
                }
            if method == 'generation':
                return {
                    "response": g_executor.chat(**args),
                }
            return {}

    s = http.server.HTTPServer(
        (server_conf['host'], server_conf['port']),
        AIServiceHTTPRequestHandler,
    )
    s.serve_forever()


if __name__ == "__main__":
    main()
