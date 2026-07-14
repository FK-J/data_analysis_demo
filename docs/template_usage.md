# 模板使用说明

本文档说明如何把本仓库作为新数据分析项目模板使用。

本文档沉淀三类核心入口：

- 新做分析项目工作流：从业务问题确认开始，到 Notebook 迭代分析、结果导出、脚本生成报告和交付审计。
- 中途修改入口：所有受管修改先更新变更执行日志，详细规则统一引用 `docs/09_change_management_standard.md`。
- 框架问题入口：只记录框架、模板、工具或流程缺陷，不与普通业务变更重复维护状态。

## 工作流总览

### 贯穿式变更与问题记录

影响业务契约、计算结果、正式产物或复现链路的修改，必须先记录到：

```text
docs/change_execution_log.md
```

该文件是修改执行状态的唯一记录。L0-L3 判级、重跑范围和完成条件统一遵循 `docs/09_change_management_standard.md`。

如果修改暴露出框架、模板、工具或流程缺陷，再同步更新 `docs/framework_issue_log.md` 并关联 `change_id`。普通业务需求和执行状态不重复写入问题日志。

### 新做分析项目工作流

新做分析项目时，必须先建立业务和交付框架，再进入数据处理和分析。推荐顺序如下：

1. 明确业务背景、决策目标、核心业务问题、预期使用者和交付形式。
2. 基于 `docs/analysis_framework_template.md` 创建 `docs/analysis_framework.md`，并与用户确认业务分析框架。
3. 基于 `docs/final_report_structure_template.md` 创建 `reports/final/final_report_structure.md`，并与用户确认最终报告呈现结构。
4. 配置 `configs/analysis_config.yaml`，并在 `docs/change_execution_log.md` 中创建项目初始化记录。
5. 查看或初始化 `docs/framework_issue_log.md`，仅作为框架、模板、工具和流程缺陷入口。
6. 如需连接数据库，复制 `configs/database.example.yaml` 为本地不提交的 `configs/database.yaml`。
7. 查看 `docs/script_catalog.md`，确认当前可执行脚本的功能、输入、输出和安全注意事项是否适用于本项目。
8. 在 `notebooks/main_analysis.ipynb` 中按章节执行数据加载、质量检查、清洗转换、探索分析、业务问题分析、可选统计或建模、稳健性检查和结果导出。
9. 将复杂 SQL 沉淀到 `sql/`，复杂 Python 逻辑沉淀到 `src/`；如修改 `scripts/` 下的可执行脚本，同步更新 `docs/script_catalog.md`。
10. 将关键图表、结果表和报告输入素材导出到标准目录。
11. 从头到尾顺序运行主 Notebook，生成最终报告，再按 `docs/08_reproducibility_audit_checklists.md` 审计交付。

日常分析可以局部调试；每次受管变更关闭时必须运行到最远受影响产物，正式交付前必须完整运行。

### 中途修改分析需求工作流

分析过程中出现新需求时，不能直接改代码、图表或报告。执行顺序如下：

1. 在 `docs/change_execution_log.md` 创建本次变更记录。
2. 按 `docs/09_change_management_standard.md` 确认等级、验收标准、影响范围、重跑起点和必达产物。
3. 契约发生变化时，先同步业务框架或报告结构；修复实现以重新符合原契约时，不改写契约。
4. 将状态改为“进行中”后实施，并从最早受影响阶段运行到最远受影响产物。
5. 更新检查结果；框架或流程存在缺陷时，另在 `docs/framework_issue_log.md` 记录根因并关联 Change ID。
6. 所有必做项完成后把记录改为“已完成”；准备交付时完整运行主 Notebook 并重新生成报告。

## 1. 初始化新项目

本节只说明从模板仓库复制到具体项目后的初始化文件操作；完整分析推进顺序以上方“新做分析项目工作流”为准。

1. 复制本模板到新项目目录。
2. 修改 `configs/analysis_config.yaml` 中的项目名称、时区、随机种子和默认数据源 profile。
3. 参考 `docs/project_readme_template.md` 重写新项目 README。
4. 删除不适用于当前项目的示例 SQL、占位说明或空目录说明。
5. 在 `docs/change_execution_log.md` 中创建项目初始化记录。
6. 保留 `docs/framework_issue_log.md`，用于记录框架、模板、工具和流程缺陷。
7. 如调整 `scripts/` 下的可执行脚本，同步更新 `docs/script_catalog.md`。

## 2. 确认业务分析框架

业务分析框架是正式分析前必须确认的业务文档，不是指标口径表。

它应该优先回答：

- 当前业务背景是什么？
- 本次分析服务什么决策？
- 需要回答哪些核心业务问题？
- 这些问题如何从业务角度拆解？
- 每个问题的分析路径是什么？
- 有哪些业务假设需要验证？
- 本次分析不覆盖什么？
- 最终报告需要支持什么行动？

指标口径、数据源、SQL 和统计方法只是支撑内容，应放在业务框架后面的支撑章节。

如果用户提出新的分析需求，必须先判断是否影响 `docs/analysis_framework.md`。如果影响，应先更新框架文档，再同步 Notebook、SQL、Python 和报告。

## 3. 确认最终报告结构

最终报告结构用于在分析前确认最终结果如何呈现。它应基于：

```text
docs/final_report_structure_template.md
```

生成：

```text
reports/final/final_report_structure.md
```

报告结构应把汇总结果放在最前面，并为每个业务问题说明：

- 本节目标。
- 具体分析逻辑。
- 预期呈现的关键结果。
- 预期图表。
- 预期结果表。
- 需要说明的口径或限制。

该文件只确认最终报告呈现内容，不负责生成洞察。

## 4. 配置数据源

如果使用数据库：

1. 复制 `configs/database.example.yaml` 为 `configs/database.yaml`。
2. 选择或新增 `profiles` 下的数据源 profile。
3. 在 `configs/analysis_config.yaml` 中设置 `analysis.database_profile`。
4. 使用环境变量或 `.env` 保存敏感连接信息。

如果只使用本地文件：

1. 将原始数据放到 `data/raw/`，或将外部参考数据放到 `data/external/`。
2. 在 Notebook 中说明数据来源、时间范围、粒度和字段含义。
3. 不需要真实数据库配置时，在 Notebook 中标注数据库部分不适用。

## 5. 编写分析流程

主流程必须通过 `notebooks/main_analysis.ipynb` 从上到下复现。

Notebook 必须基于 `docs/analysis_framework.md` 和 `reports/final/final_report_structure.md` 展开，不能绕过业务框架和报告结构直接进入数据处理或图表展示。

推荐分工：

- `sql/extract/`：数据抽取 SQL。
- `sql/transform/`：数据转换 SQL。
- `sql/validation/`：数据校验 SQL。
- `src/db/`：数据库连接和 SQL 执行。
- `src/io/`：本地文件读写。
- `src/quality/`：数据质量检查。
- `src/cleaning/`：数据清洗。
- `src/features/`：特征或分析宽表构建。
- `src/analysis/`：业务指标和分析逻辑。
- `src/stats/`：统计检验。
- `src/modeling/`：机器学习建模。
- `src/visualization/`：图表样式和绘图函数。
- `src/reporting/`：结果导出和报告素材生成。

Notebook 负责串联流程、展示关键结果和记录业务解释。

## 6. 维护脚本功能目录

可直接执行脚本的功能和使用方式统一记录在：

```text
docs/script_catalog.md
```

分析过程中，如果需要快速执行某个脚本，应先查看该文档，确认脚本的输入、输出、是否会写文件以及安全注意事项。

如发生以下任一情况，必须同步更新 `docs/script_catalog.md`：

- 新增 `scripts/` 下的可执行脚本。
- 删除或重命名 `scripts/` 下的脚本。
- 修改脚本参数、默认输入、默认输出、写文件行为或安全边界。
- 将原本只能由 Notebook 调用的逻辑改为可单独执行脚本。

## 7. 输出交付物

推荐输出路径：

```text
reports/figures/    图表
reports/tables/     结果表
reports/final/      最终报告或交付材料
logs/               运行日志和审计记录
```

关键结论不能只存在于 Notebook 输出缓存中，必须有可追溯的图表、结果表或报告文件。

最终报告结构应参考：

```text
docs/final_report_structure_template.md
```

Notebook 或分析脚本需要导出报告输入素材：

```text
reports/final/report_inputs.yaml
```

输入格式参考：

```text
docs/report_inputs_template.yaml
```

最终报告由脚本生成：

```bash
python scripts/generate_final_report.py
```

正式交付前，先从头到尾顺序运行主 Notebook，再执行上述报告生成命令。

具体项目交付文件保存为：

```text
reports/final/final_analysis_report.md
```

报告默认只呈现结果、图表、表格、口径和输出文件路径，不自动生成洞察或业务解读。

如需渲染已准备好的洞察内容，必须由用户明确要求，并显式运行：

```bash
python scripts/generate_final_report.py --with-insights
```

## 8. 提交前检查

提交前检查项统一维护在：

```text
docs/08_reproducibility_audit_checklists.md
```

本文档不重复维护检查清单。提交前至少应确认已按该文档完成项目完成检查、最低交付标准检查、禁止事项检查和交付前审计流程，并通过 `docs/09_change_management_standard.md` 的发布门禁。
