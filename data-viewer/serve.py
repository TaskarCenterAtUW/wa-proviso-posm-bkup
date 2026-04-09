#!/usr/bin/env python3
"""Static file server with Range support for local PMTiles testing."""

# Why this file exists:
# - opening the viewer with file:// blocks fetch() for PMTiles/index JSON
# - PMTiles readers need HTTP byte-range requests to read archive chunks
# - this small server gives a predictable local test path for tdei-viewer.html

import http.server
import os
import sys


PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765


class RangeRequestHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            return super().send_head()

        range_header = self.headers.get("Range")
        if not range_header:
            return super().send_head()

        try:
            file_size = os.path.getsize(path)
            _, byte_range = range_header.split("=", 1)
            start_str, _, end_str = byte_range.partition("-")
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
            end = min(end, file_size - 1)
            length = end - start + 1
        except Exception:
            self.send_error(416, "Range Not Satisfiable")
            return None

        try:
            handle = open(path, "rb")
        except OSError:
            self.send_error(404, "File not found")
            return None

        handle.seek(start)
        self.range = (start, end, length)
        self.send_response(206, "Partial Content")
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        return handle

    def copyfile(self, source, outputfile):
        if hasattr(self, "range"):
            _, _, length = self.range
            remaining = length
            while remaining > 0:
                chunk = source.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
            return
        super().copyfile(source, outputfile)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with http.server.ThreadingHTTPServer(("", PORT), RangeRequestHandler) as server:
        print(f"Serving http://localhost:{PORT}/")
        print(f"Open http://localhost:{PORT}/tdei-viewer.html")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
