"""Execute two versions of a small workflow and write a demo atlas."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from subprocess import run
from sys import executable
from uuid import uuid4

from build_atlas import render, write_document


def demo():
    raw = '["A", " A", "B"]'
    source = "demo_walkthrough.py · 统计规则"
    description = '三个记录 "A"、" A"、"B"。'
    attempts = []
    for number, rule in enumerate(("values", "(value.strip() for value in values)"), start=1):
        code = (
            "from collections import Counter\n"
            "import json, sys\n"
            "values = json.loads(sys.stdin.read())\n"
            f"print(json.dumps(Counter({rule}), indent=2))\n"
        )
        first = number == 1
        expected = "保留原样，两个写法分开计数。" if first else "忽略首尾空格，将两条 A 合并。"
        measured = run([executable, "-I", "-c", code], input=raw, capture_output=True,
                       encoding="utf-8", check=True, timeout=10)
        counts = json.loads(measured.stdout)
        attempts.append({
            "id": f"count-{number}", "run_id": uuid4().hex,
            "code_version": sha256(code.encode()).hexdigest(), "input_id": sha256(raw.encode()).hexdigest(),
            "source": source, "code": code, "input": description, "expected": expected,
            "advice": "对照结果里 A 有几个写法，各有多少条。",
            "result": f"实际统计出 {len(counts)} 个类别，合计 {sum(counts.values())} 条记录。",
            "output": measured.stdout.strip(),
            "change": "首次执行原统计规则。" if first else "示范修改。统计前去掉首尾空格。",
        })
    return {
        "title": "样例 · 从记录到统计",
        "nodes": [
            {"id": "input", "title": "样本记录", "group": "输入", "summary": description, "position": [1, 1]},
            {"id": "count", "title": "统计类别", "group": "处理", "summary": "按类别累计次数。", "position": [1, 2]},
            {"id": "report", "title": "生成报告", "group": "输出", "summary": "把计数写成报告。", "position": [1, 3]},
        ],
        "edges": [
            {"from": "input", "to": "count", "label": "记录", "detail": "交给统计代码做分组。"},
            {"from": "count", "to": "report", "label": "计数", "detail": "把统计结果传入报告步骤。"},
        ],
        "walkthrough": {
            "id": "demo", "title": "一起核对一轮统计",
            "steps": [
                {"id": "count", "title": "统计类别", "node": "count", "source": source,
                 "input": description, "expected": "显示每个类别的次数。", "attempts": attempts},
                {"id": "report", "title": "生成报告", "node": "report", "source": "报告入口待接入",
                 "input": "类别与次数", "expected": "生成可阅读的报告。", "attempts": []},
            ],
        },
    }


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="new demo JSON file")
    args = parser.parse_args()
    try:
        data = demo()
        render(data)
        write_document(args.output, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
