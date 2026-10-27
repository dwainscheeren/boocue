"""Serve the isolated UI preview with synthetic devices on localhost."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "/dev/preview.html"
        elif self.path.startswith("/boocue_frontend/"):
            self.path = self.path.replace("/boocue_frontend/", "/custom_components/boocue/frontend/", 1)
        elif self.path.startswith("/assets/"):
            self.path = self.path.replace("/assets/", "/custom_components/boocue/assets/", 1)
        return super().do_GET()


if __name__ == "__main__":
    print("BooCue isolated UI preview: http://127.0.0.1:8176", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8176), partial(Handler, directory=str(ROOT))).serve_forever()
