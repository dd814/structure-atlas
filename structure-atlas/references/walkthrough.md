# 实跑与批注

「一起跑」把现有图谱和项目的一次实际执行连接起来。左边看代码、输入和跑前预期，右边看同一次执行的输出。批注保存在本机，用户在 Agent 聊天说「读批注」即可继续。

## 先跑示例

在可写的工作目录执行以下命令，将 `<skill-dir>` 换成技能目录。只需 Python 3.10+。

```text
python "<skill-dir>/scripts/demo_walkthrough.py" demo.json
python "<skill-dir>/scripts/serve_atlas.py" demo.json
```

打开第二条命令打印的地址，点「一起跑」。示例用同一份记录实际执行两个版本的统计代码，可以切换运行查看两个结果。写一条批注并刷新，之后切换运行，检查批注仍属于刚才选择的执行。退出服务使用 Ctrl+C。

## 接入项目

1. 在图谱 JSON 的 `walkthrough.steps` 按流程登记步骤。先准备一个能独立执行的入口。记录当前代码位置、输入、跑前预期和一两个验收点。其余步骤先以空 `attempts` 留出位置。
2. 走项目正常入口，观察真实输出与失败状态。用下面的字段追加一条运行，选择真正能核对结果的证据，例如查询结果、日志摘录或固定到本次运行的本地预览页。保存代码版本与正在执行的文件片段，并确认输入标识。页面刷新后会读取更新后的 JSON，历史链接仍可打开。
3. 通过 `serve_atlas.py <map.json>` 为同一份数据启用批注。可用 `--notes <file>` 指定文件，默认在输入 JSON 旁写入 `<文件名>.feedback.json`。已有本地工作台可复用其服务端，确保用下列字段查验归属再保存。离线 HTML 同样能读取已嵌入的实跑记录。
4. Agent 读批注时，按运行编号、代码版本和输入标识回到证据。只有获得对应修改指令后才改代码。之后沿用输入，追加一条有新运行编号的记录，用 `change` 写清改动和依据。检查旧批注能从旧运行进入、新运行的预览和现状图一致，再同步当前项目进展。

| 对象 | 字段 |
|---|---|
| `walkthrough` | `id` 持久标识、`title` 标题、`steps` 步骤数组。 |
| 步骤 | `id`、`title`、`node` 对应图谱部件、`source` 文件与行号、`input` 样本和相关参数、`expected` 预期、可选 `advice`、`attempts` 运行数组，按执行顺序填写。 |
| 运行 | `id`（步骤内唯一）、`run_id`（全图唯一的实际运行编号）、`code_version`（提交或文件指纹）、`input_id`（内容指纹或可核对的输入版本）、`source`、`code`、`input`、`expected`、`result`。可选 `advice`、`change`，以及至少一项 `output`（实际输出文本）或 `preview_url`。 |
| 批注 | 每条有 `walkthrough_id`、`step_id`、`attempt_id`、`run_id`、`code_version`、`input_id`、`id`、`text`、`created`。 |

`id` 和 `run_id` 可用字母、数字、点、短横线或下划线，以字母或数字开头。带运行标识的地址形如 `/#walkthrough/import/import-1`。使用 `preview_url` 时提供项目自己的 `http://127.0.0.1:<port>/…` 结果地址，确保它显示固定运行。预览应用允许嵌入时，可在右列直接查看，也可单独打开。示例脚本生成可检查的完整输入。

分享前检查运行文本、代码快照和图谱 JSON，按目的地选取可公开内容。批注文件属于运行数据，单独保存。
