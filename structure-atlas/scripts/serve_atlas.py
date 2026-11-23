"""Serve one local atlas and persist feedback against recorded runs."""
from argparse import ArgumentParser
from datetime import datetime, timezone
from hmac import compare_digest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
from secrets import token_hex
from threading import Lock
from urllib.parse import parse_qs, urlsplit

from build_atlas import render, write_document


KEYS = ("walkthrough_id", "step_id", "attempt_id", "run_id", "code_version", "input_id")


def identities(data):
    plan = data.get("walkthrough", {})
    for step in plan.get("steps", []):
        for run in step["attempts"]:
            yield dict(zip(KEYS, (plan["id"], step["id"], run["id"], run["run_id"],
                                  run["code_version"], run["input_id"])))


class FeedbackStore:
    def __init__(self, path):
        self.path = path
        self.lock = Lock()

    def notes(self, scope, draft=None):
        with self.lock:
            try:
                entries = json.loads(self.path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                entries = []
            if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
                raise ValueError("批注文件格式有误。")
            matching = [entry for entry in entries if all(entry.get(key) == scope[key] for key in KEYS)]
            if draft is None:
                return matching
            previous = next((entry for entry in matching if entry["id"] == draft["id"]), None)
            if previous:
                if previous["text"] != draft["text"]:
                    raise ValueError("这条提交已存在，请重新写一条批注。")
                return matching
            note = {**scope, **draft, "created": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            write_document(self.path, json.dumps(entries + [note], ensure_ascii=False, indent=2) + "\n",
                           overwrite=True)
            return matching + [note]


def handler_for(atlas, store):
    token = token_hex(32)

    class Handler(BaseHTTPRequestHandler):
        def read_atlas(self):
            return json.loads(atlas.read_text(encoding="utf-8-sig"))

        def reply(self, status, body, kind="application/json; charset=utf-8"):
            if not isinstance(body, str):
                body = json.dumps(body, ensure_ascii=False)
            payload = body.encode()
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *_):
            # Internal URLs identify private runs. Keep them out of the console.
            pass

        def do_GET(self):
            self.dispatch()

        def do_POST(self):
            self.dispatch(save=True)

        def dispatch(self, save=False):
            host = f"127.0.0.1:{self.server.server_port}"
            if self.headers.get("Host") != host:
                self.reply(403, {"error": "请通过服务打印的本机地址打开。"})
                return
            path = urlsplit(self.path)
            if path.path == "/" and not save:
                try:
                    document = render(self.read_atlas()).replace(
                        '<head>', '<head><meta name="atlas-live" content="true">', 1)
                    self.reply(200, document, "text/html; charset=utf-8")
                except (OSError, ValueError):
                    self.reply(500, {"error": "无法读取有效的图谱数据。"})
                return
            if path.path != "/feedback":
                self.reply(404, {"error": "页面不存在。"})
                return
            if save and (self.headers.get("Origin") != f"http://{host}" or
                         not compare_digest(self.headers.get("X-Atlas-Token", "").encode(), token.encode())):
                self.reply(403, {"error": "保存权限已失效，请刷新页面。"})
                return
            try:
                query = parse_qs(path.query, max_num_fields=len(KEYS))
                if set(query) != set(KEYS) or any(len(values) != 1 for values in query.values()):
                    raise ValueError("批注缺少运行标识。")
                scope = {key: query[key][0] for key in KEYS}
                if scope not in identities(self.read_atlas()):
                    self.reply(409, {"error": "这次运行已变化，请刷新图谱。"})
                    return
                draft = self.read_draft() if save else None
                self.reply(200, {"notes": store.notes(scope, draft), "token": token})
            except (ValueError, TypeError, KeyError) as error:
                self.reply(400, {"error": str(error)})
            except OSError:
                self.reply(500, {"error": "无法访问本地图谱或批注文件。"})

        def read_draft(self):
            length = int(self.headers.get("Content-Length", 0))
            if self.headers.get_content_type() != "application/json" or not 0 < length <= 16000:
                raise ValueError("批注请求格式有误。")
            draft = json.loads(self.rfile.read(length))
            if not isinstance(draft, dict) or set(draft) != {"id", "text"}:
                raise ValueError("批注请求缺少编号或内容。")
            identifier = draft["id"]
            note = draft["text"]
            if not isinstance(identifier, str) or not re.fullmatch(r"[0-9a-f-]{36}", identifier):
                raise ValueError("批注编号有误。")
            if not isinstance(note, str) or not 0 < len(note.strip()) <= 2000:
                raise ValueError("批注应包含 1 到 2000 个字符。")
            return {"id": identifier, "text": note.strip()}

    return Handler


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("atlas", type=Path, help="maintained atlas JSON")
    parser.add_argument("--notes", type=Path, help="feedback JSON, defaults to <atlas>.feedback.json")
    parser.add_argument("--port", type=int, default=0, help="IPv4 loopback port, 0 picks an available port")
    args = parser.parse_args()
    notes = args.notes or args.atlas.with_suffix(".feedback.json")
    if args.atlas.resolve() == notes.resolve():
        parser.error("Atlas input and feedback must be separate files")
    try:
        render(json.loads(args.atlas.read_text(encoding="utf-8-sig")))
        handler = handler_for(args.atlas.resolve(), FeedbackStore(notes.resolve()))
        with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
            print(f"http://127.0.0.1:{server.server_port}/", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
