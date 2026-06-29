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
| `scripts/generate_final_report.py` | 根据结构化输入生成最终分析报告 | `python scripts/generate_final_report.py` | 是 |

## 3. 脚本详情

### 3.1 `scripts/generate_final_report.py`

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
