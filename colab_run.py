"""Run the app inside Google Colab and open it via Colab's built-in proxy.

Colab cell usage:

    !pip install -q -r requirements.txt
    %run colab_run.py

The server binds to 127.0.0.1 (no 0.0.0.0); Colab's proxy forwards the port.
"""

import threading

from werkzeug.serving import make_server

from app import app

PORT = 5000
server = make_server("127.0.0.1", PORT, app)
threading.Thread(target=server.serve_forever, daemon=True).start()

try:
    from google.colab.output import eval_js  # type: ignore

    print("Open:", eval_js(f"google.colab.kernel.proxyPort({PORT})"))
except ImportError:
    print(f"Open: http://127.0.0.1:{PORT}")
