import http.server
import json

import click

from tok715.misc.config import load_config


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
def main(opt_conf):
    conf = load_config(opt_conf)

    server_conf = conf["ai_service"]["server"]

    class AIServiceHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
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
                # TODO: handle incoming message
                self.send_json(self.read_json())
            except Exception as e:
                self.send_json({"error": str(e)}, code=500)

    s = http.server.HTTPServer((server_conf['host'], server_conf['port']), AIServiceHTTPRequestHandler)
    s.serve_forever()


if __name__ == "__main__":
    main()
