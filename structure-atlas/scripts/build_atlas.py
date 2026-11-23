"""Validate a relationship atlas and build a self-contained HTML document."""
import argparse
from datetime import date
import html
import json
from pathlib import Path
from tempfile import NamedTemporaryFile


KINDS = {"actual", "experimental", "planned", "uncertain"}
UPDATE_STATES = {"verified", "implemented", "blocked", "planned"}


def text(record, field, where, optional=False):
    value = record.get(field, "" if optional else None)
    if not isinstance(value, str) or (not optional and not value.strip()):
        raise ValueError(f"{where}.{field} must be {'text' if optional else 'nonempty text'}")
    return value


def array(record, field, where, optional=False):
    value = record.get(field, [] if optional else None)
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{where}.{field} must be an array of objects")
    return value


def validate_checkpoints(data, ids):
    previous = ""
    for index, checkpoint in enumerate(array(data, "checkpoints", "atlas", optional=True)):
        where = f"checkpoints[{index}]"
        stamp = text(checkpoint, "date", where)
        try:
            parsed = date.fromisoformat(stamp)
        except ValueError:
            raise ValueError(f"{where}.date must use YYYY-MM-DD") from None
        if parsed.isoformat() != stamp or stamp < previous:
            raise ValueError(f"{where}.date must use YYYY-MM-DD in chronological order")
        previous = stamp
        text(checkpoint, "title", where)
        changes = array(checkpoint, "changes", where)
        if not changes:
            raise ValueError(f"{where}.changes must include at least one update")
        seen = set()
        for number, change in enumerate(changes):
            location = f"{where}.changes[{number}]"
            node = text(change, "node", location)
            if node not in ids or node in seen:
                raise ValueError(f"{location}.node must name a known node once per checkpoint")
            seen.add(node)
            status = text(change, "status", location)
            if status not in UPDATE_STATES:
                raise ValueError(f"{location}.status must be one of {', '.join(sorted(UPDATE_STATES))}")
            text(change, "note", location)
            text(change, "evidence", location, optional=status != "verified")
            text(change, "next", location, optional=True)


def validate(data):
    if not isinstance(data, dict):
        raise ValueError("Atlas input must be a JSON object")
    text(data, "title", "atlas")
    text(data, "intro", "atlas", optional=True)
    nodes = array(data, "nodes", "atlas")
    if not nodes:
        raise ValueError("An atlas needs at least one node")
    ids = set()
    positions = set()
    for index, node in enumerate(nodes):
        where = f"nodes[{index}]"
        identifier = text(node, "id", where)
        if identifier in ids:
            raise ValueError(f"Duplicate node id: {identifier}")
        ids.add(identifier)
        for field in ("title", "group", "summary"):
            text(node, field, where)
        text(node, "source", where, optional=True)
        if "position" in node:
            position = node["position"]
            if (not isinstance(position, list) or len(position) != 2
                    or any(type(part) is not int for part in position)
                    or not (1 <= position[0] <= 12 and 1 <= position[1] <= 4)):
                raise ValueError(f"{where}.position must be [row 1–12, column 1–4]")
            if tuple(position) in positions:
                raise ValueError(f"Duplicate overview position: {position}")
            positions.add(tuple(position))
        for number, block in enumerate(array(node, "blocks", where, optional=True)):
            location = f"{where}.blocks[{number}]"
            for field in ("title", "summary"):
                text(block, field, location)
            for field in ("source", "code"):
                text(block, field, location, optional=True)
    edges = array(data, "edges", "atlas")
    for index, edge in enumerate(edges):
        where = f"edges[{index}]"
        sender, receiver = (text(edge, field, where) for field in ("from", "to"))
        if sender not in ids or receiver not in ids or sender == receiver:
            raise ValueError(f"{where} must connect two distinct known nodes")
        for field in ("label", "detail"):
            text(edge, field, where)
        kind = text(edge, "kind", where, optional=True)
        if kind and kind not in KINDS:
            raise ValueError(f"{where}.kind must be one of {', '.join(sorted(KINDS))}")
        text(edge, "evidence", where, optional=True)
        if "diagram" in edge and type(edge["diagram"]) is not bool:
            raise ValueError(f"{where}.diagram must be true or false")
    paths = array(data, "paths", "atlas", optional=True)
    for index, path in enumerate(paths):
        where = f"paths[{index}]"
        text(path, "title", where)
        steps = array(path, "steps", where)
        if not steps:
            raise ValueError(f"{where} needs at least one step")
        for number, step in enumerate(steps):
            location = f"{where}.steps[{number}]"
            if text(step, "node", location) not in ids:
                raise ValueError(f"{location}.node must name a known node")
            text(step, "note", location)
    validate_checkpoints(data, ids)


def write_document(output, document, overwrite=False):
    if not overwrite:
        with output.open("x", encoding="utf-8", newline="") as result:
            result.write(document)
        return
    staging = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=output.parent,
                                prefix=f".{output.stem}-", suffix=".tmp", delete=False) as result:
            staging = Path(result.name)
            result.write(document)
        staging.replace(output)
    finally:
        if staging is not None:
            staging.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="UTF-8 atlas JSON")
    parser.add_argument("output", type=Path, help="destination HTML file")
    parser.add_argument("--force", action="store_true", help="replace an existing output")
    args = parser.parse_args()
    try:
        if args.output.resolve() == args.input.resolve():
            raise ValueError("Input and output must be different paths")
        data = json.loads(args.input.read_text(encoding="utf-8-sig"))
        validate(data)
        assets = Path(__file__).resolve().parents[1] / "assets"
        payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        payload = payload.replace("<", r"\u003c").replace(">", r"\u003e").replace("&", r"\u0026")
        document = (assets / "atlas.html").read_text(encoding="utf-8")
        document = document.replace("__ATLAS_PROGRESS_CSS__", (assets / "progress.css").read_text(encoding="utf-8"), 1)
        document = document.replace("__ATLAS_PROGRESS_JS__", (assets / "progress.js").read_text(encoding="utf-8"), 1)
        document = document.replace("__ATLAS_JSON__", payload, 1)
        document = document.replace("__ATLAS_TITLE__", html.escape(data["title"]), 1)
        write_document(args.output, document, args.force)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"{len(data['nodes'])} nodes, {len(data['edges'])} relations")


if __name__ == "__main__":
    main()
