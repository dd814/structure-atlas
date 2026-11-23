# Structure Atlas · 复杂结构图谱

用关系总图、具体路径和可展开的细节解释代码库、系统架构或业务流程。在同一份 HTML 上追踪进展，或和 Agent 一起对照代码、预期和真实运行结果。

## 安装

从 [Releases](https://github.com/dd814/structure-atlas/releases) 下载任一版本的源码。把里面完整的 `structure-atlas/` 目录复制到 Codex 的技能目录（默认 `~/.codex/skills/`）。安装后应能找到 `~/.codex/skills/structure-atlas/SKILL.md`。

在 Agent 中调用 [`$structure-atlas`](structure-atlas/SKILL.md)，可以直接说「画清这个项目从输入到输出怎么走」或「带我实跑导入，记录我对这次结果的批注」。

## 本地体验

从仓库根目录运行下列命令，使用 Python 3.10 或更新版本。

```sh
python structure-atlas/scripts/demo_walkthrough.py demo.json
python structure-atlas/scripts/serve_atlas.py demo.json
```

打开命令打印的本机地址，点「一起跑」。用同一份样本执行的两个版本都能查看。批注保存后，在 Agent 聊天说「读批注」即可继续。接入自己的项目时，参见[实跑与批注](structure-atlas/references/walkthrough.md)。仅制作离线结构图时，参见[图谱模板](structure-atlas/references/html-template.md)。

## 版本

| 版本 | 内容 |
|---|---|
| [1.2.0](https://github.com/dd814/structure-atlas/releases/tag/structure-atlas-v1.2.0) | 新增「一起跑」。实跑结果、历史代码和本机批注绑定到同一次运行。 |
| [1.1.0](https://github.com/dd814/structure-atlas/releases/tag/structure-atlas-v1.1.0) | 新增项目进展、部件旁的最新标注、历史记录和讨论上下文复制。 |
| [1.0.0](https://github.com/dd814/structure-atlas/releases/tag/structure-atlas-v1.0.0) | 提供关系总图、阅读路径、分层细节和离线 HTML。 |
