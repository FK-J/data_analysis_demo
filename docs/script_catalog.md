# 脚本功能目录与使用规范

本文档记录 `scripts/` 目录下可直接执行脚本的功能、输入、输出和使用规范，方便分析过程中快速定位并运行某个功能脚本。

当新增、删除、重命名或修改 `scripts/` 下的脚本时，必须同步更新本文档。Agent 在执行涉及脚本的任务时，应先查看本文档；如果脚本文档与实际脚本不一致，应优先修正文档或提醒用户确认。

## 1. 维护规则

- 每个可直接执行的脚本都必须在本文档登记。
- 只被其他模块 import、不能直接运行的辅助模块，不登记在本文档中；如果放在 `scripts/` 下，应说明原因。
- 新增脚本时，先补充本文档，再在 README、Notebook 或交付说明中引用对应命令。
- 修改脚本参数、默认输入、默认输出、写文件行为或安全边界时，必须同步更新本文档。
- 删除或重命名脚本时，必须同步删除或修改本文档中的对应条目。
- 涉及数据库写入、覆盖文件、删除文件、调用外部服务或处理敏感数据的脚本，必须在“安全与注意事项”中明确说明。

## 2. 快速索引

| 脚本 | 功能 | 常用命令 | 是否可单独运行 |
| --- | --- | --- | --- |
| `scripts/init_project.py` | 从模板初始化具体分析项目 | `python scripts/init_project.py --help` | 是 |
| `scripts/generate_notebook.py` | 根据项目契约生成主 Notebook 骨架 | `python scripts/generate_notebook.py` | 是 |
| `scripts/validate_project.py` | 检查结构、配置、Notebook、SQL 和安全规则 | `python scripts/validate_project.py` | 是 |
| `scripts/run_notebook.py` | 在干净内核中执行主 Notebook 并保存证据 | `python scripts/run_notebook.py` | 是 |
| `scripts/audit_project.py` | 审计执行证据和预期交付物 | `python scripts/audit_project.py` | 是 |
| `scripts/generate_final_report.py` | 根据结构化输入生成最终分析报告 | `python scripts/generate_final_report.py` | 是 |

## 3. 脚本详情

### 3.1 `scripts/init_project.py`

**功能：** 从当前模板复制并初始化一个具体的数据分析项目。

**默认输入：** 当前模板目录，以及必填参数 `--output`、`--name`、`--display-name`。

**默认输出：** `--output` 指定的新项目目录，包括项目契约、确认文档和按配置生成的主 Notebook。

**常用命令：**

```bash
python scripts/init_project.py --output ../new_analysis_project --name new_analysis_project --display-name "新数据分析项目"
```

**是否必须由 Notebook 调用：** 否，仅用于项目初始化。

**是否会写文件：** 会创建新项目目录；目标目录已存在且非空时不得覆盖。

**安全与注意事项：** `--output` 应位于模板仓库之外，初始化后仍需人工确认业务分析框架和报告结构。

### 3.2 `scripts/generate_notebook.py`

**功能：** 根据 `project.yaml` 和 `templates/notebook_sections.yaml` 生成主 Notebook 骨架。

**默认输入：** 项目根目录下的项目契约和章节模板。

**默认输出：** `project.yaml` 中 `runtime.notebook` 指定的 Notebook。

**常用命令：**

```bash
python scripts/generate_notebook.py
```

**是否必须由 Notebook 调用：** 否，仅用于初始化或已审阅影响的结构调整。

**是否会写文件：** 会覆盖目标 Notebook。

**安全与注意事项：** 正式分析后重新生成前必须登记变更并审阅覆盖影响。

### 3.3 `scripts/validate_project.py`

**功能：** 校验项目契约、必需路径、Notebook 章节、占位内容、只读 SQL、安全文件和报告输入。

**默认输入：** 当前项目目录。

**默认输出：** 终端检查结果；传入 `--json-output` 时额外写入 JSON 报告。

**常用命令：**

```bash
python scripts/validate_project.py
```

**是否必须由 Notebook 调用：** 否，属于 Notebook 外围质量门禁。

**是否会写文件：** 默认不会；仅在指定 `--json-output` 时写文件。

**安全与注意事项：** 检查通过不替代业务口径和分析结果的人工复核。

### 3.4 `scripts/run_notebook.py`

**功能：** 先执行项目预检，再在干净内核中从头运行主 Notebook 并保存复现证据。

**默认输入：** `project.yaml` 指定的主 Notebook。

**默认输出：** `logs/runs/<run_id>/executed_main_analysis.ipynb` 和 `manifest.json`。

**常用命令：**

```bash
python scripts/run_notebook.py
```

**是否必须由 Notebook 调用：** 否，属于正式复现门禁。

**是否会写文件：** 会写入执行副本和运行清单。

**安全与注意事项：** 无界面执行不替代分析师的交互分析；失败时仍保留运行清单用于定位。

### 3.5 `scripts/audit_project.py`

**功能：** 审计最近一次 Notebook 执行证据和项目声明的交付物。

**默认输入：** 项目契约、运行清单及 `reports/` 下的交付文件。

**默认输出：** `logs/audit_report.json`。

**常用命令：**

```bash
python scripts/audit_project.py
```

**是否必须由 Notebook 调用：** 否，属于交付审计门禁。

**是否会写文件：** 会写入审计报告；具体项目通过审计后还会更新本地 Harness 状态。

**安全与注意事项：** 必须在成功完成无界面 Notebook 运行后执行。

### 3.6 `scripts/generate_final_report.py`

**功能：** 根据 `reports/final/report_inputs.yaml` 生成结果呈现型最终分析报告。

**适用场景：** Notebook 已完成关键图表、结果表和报告输入素材导出后，生成最终交付报告。

**默认输入：**

- `reports/final/report_inputs.yaml`
- `reports/final/final_report_structure.md`

**默认输出：**

- `reports/final/final_analysis_report.md`

**常用命令：**

```bash
python scripts/generate_final_report.py
```

如需指定输入和输出路径：

```bash
python scripts/generate_final_report.py \
  --input reports/final/report_inputs.yaml \
  --output reports/final/final_analysis_report.md
```

如用户明确要求渲染已准备好的洞察内容：

```bash
python scripts/generate_final_report.py --with-insights
```

**是否必须由 Notebook 调用：** 否。该脚本可以单独运行，但输入素材应由 Notebook 或分析流程先生成。

**是否会写文件：** 会写入 `reports/final/final_analysis_report.md`，如果输出文件已存在会覆盖。

**安全与注意事项：**

- 默认只呈现结果、图表、表格、口径和输出文件路径。
- 默认不调用大模型，不自动生成洞察、归因或业务建议。
- 只有显式传入 `--with-insights` 时，才会渲染 `report_inputs.yaml` 中已经写好的洞察文本。
- 运行前应检查 `report_inputs.yaml` 是否仍有“待填写”占位内容，以及是否包含不应进入报告的敏感明细信息。

## 4. 新增脚本登记模板

新增脚本时，复制以下模板到“脚本详情”并填写。

````markdown
### X.X `scripts/example_script.py`

**功能：** 待填写。

**适用场景：** 待填写。

**默认输入：**

- 待填写。

**默认输出：**

- 待填写。

**常用命令：**

```bash
python scripts/example_script.py
```

**是否必须由 Notebook 调用：** 是/否，说明原因。

**是否会写文件：** 是/否，说明写入路径和覆盖规则。

**安全与注意事项：**

- 待填写。
````
