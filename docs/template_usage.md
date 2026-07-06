# 模板使用说明

本文档说明如何把本仓库作为新数据分析项目模板使用。

本文档沉淀两类核心工作流：

- 新做分析项目工作流：从业务问题确认开始，到 Notebook 迭代分析、结果导出、脚本生成报告和交付审计。
- 中途修改分析需求工作流：当分析过程中出现新问题、新口径、新数据范围或新报告呈现要求时，先判断影响范围，再同步更新业务框架、报告结构、Notebook、SQL、Python、脚本目录和输出文件。
- 贯穿式使用问题记录：在项目使用过程中持续记录用户反馈、流程卡点和框架改进建议，而不是等交付审计后再总结。

## 工作流总览

### 贯穿式使用问题记录

整个分析过程中，如果出现不满足用户需求、需要用户指导修改、流程不清楚、文档不足、脚本难用、Notebook 调试不顺或其他影响交付效率的问题，必须及时记录到：

```text
docs/framework_issue_log.md
```

记录时应说明问题发生阶段、当前影响、临时处理方式，并判断它是项目特定问题、框架通用问题还是待判断问题。

如果问题会影响当前分析结果或最终报告，必须在同一轮修改中同步更新受影响的 Notebook、SQL、Python、报告输入素材和最终报告。如果问题属于框架通用问题，应在记录中写明建议修改的文档、模板、Notebook 或脚本，但是否立即修改框架需要结合当前交付节奏和用户确认判断。

### 新做分析项目工作流

新做分析项目时，必须先建立业务和交付框架，再进入数据处理和分析。推荐顺序如下：

1. 明确业务背景、决策目标、核心业务问题、预期使用者和交付形式。
2. 基于 `docs/analysis_framework_template.md` 创建 `docs/analysis_framework.md`，并与用户确认业务分析框架。
3. 基于 `docs/final_report_structure_template.md` 创建 `reports/final/final_report_structure.md`，并与用户确认最终报告呈现结构。
4. 查看或初始化 `docs/framework_issue_log.md`，作为项目使用过程中的持续问题记录入口。
5. 配置 `configs/analysis_config.yaml`；如需连接数据库，复制 `configs/database.example.yaml` 为本地不提交的 `configs/database.yaml`。
6. 查看 `docs/script_catalog.md`，确认当前可执行脚本的功能、输入、输出和安全注意事项是否适用于本项目。
7. 在 `notebooks/main_analysis.ipynb` 中按章节执行数据加载、质量检查、清洗转换、探索分析、业务问题分析、可选统计或建模、稳健性检查和结果导出；遇到用户反馈、流程卡点或临时绕行时，同步更新 `docs/framework_issue_log.md`。
8. 将复杂 SQL 沉淀到 `sql/`，复杂 Python 逻辑沉淀到 `src/`；如新增、删除、重命名或修改 `scripts/` 下的可执行脚本，同步更新 `docs/script_catalog.md`。
9. 将关键图表、结果表和报告输入素材导出到 `reports/figures/`、`reports/tables/` 和 `reports/final/report_inputs.yaml`。
10. 运行 `python scripts/generate_final_report.py` 生成 `reports/final/final_analysis_report.md`。
11. 交付前按 `docs/08_reproducibility_audit_checklists.md` 检查 Notebook 顺序执行、输出文件、脚本目录、问题记录、报告和敏感信息。

日常分析过程中，Notebook 可以围绕某个中间步骤局部调试和重跑；但交付前必须从头到尾顺序执行一次，确认最终结果可复现。

### 中途修改分析需求工作流

分析过程中如果用户提出新的分析需求，不能直接改代码或图表。必须先判断需求变更影响范围，再同步相关文档和产物。推荐顺序如下：

1. 先判断新需求是否影响业务目标、核心业务问题、分析边界、业务假设或分析路径。
2. 判断本次修改是否源于用户使用问题、流程卡点、输出不符合预期或框架不足；如是，同步更新 `docs/framework_issue_log.md`。
3. 如果影响业务框架，先更新 `docs/analysis_framework.md`，并在其中的“需求变更记录”中记录变更内容、影响的问题/假设和同步状态。
4. 如果影响报告章节、呈现顺序、汇总方式、预期图表或预期结果表，同步更新 `reports/final/final_report_structure.md`。
5. 判断需要重跑的 Notebook 范围：数据源或时间范围变化时，从数据加载和质量检查开始；清洗规则变化时，从数据清洗与转换开始；指标口径变化时，从指标计算和业务问题分析开始；仅报告呈现变化时，通常从报告输入素材导出和最终报告生成开始。
6. 同步修改受影响的 SQL、`src/` 复用逻辑、Notebook 分析章节和报告输入素材。
7. 如果变更涉及 `scripts/` 下的可执行脚本，必须同步更新 `docs/script_catalog.md`。
8. 重新生成受影响的图表、结果表和 `reports/final/report_inputs.yaml`。
9. 重新运行 `python scripts/generate_final_report.py`，更新最终输出的 `reports/final/final_analysis_report.md`。
10. 检查最终分析报告是否已经反映本次需求变更，包括章节结构、关键结果、图表、表格、口径限制和输出文件路径。
11. 如果本次变更暴露出框架通用问题，在 `docs/framework_issue_log.md` 中补充框架修改建议和关联文件。
12. 交付前再次检查新增或变更需求是否已同步到业务框架、报告结构、Notebook、SQL、Python、脚本目录、问题记录和最终报告。

需求变更后可以先局部重跑受影响章节；但进入交付前，仍必须完整顺序运行主 Notebook，避免隐藏状态、旧缓存或新旧结果混用。

## 1. 初始化新项目

本节只说明从模板仓库复制到具体项目后的初始化文件操作；完整分析推进顺序以上方“新做分析项目工作流”为准。

1. 复制本模板到新项目目录。
2. 修改 `configs/analysis_config.yaml` 中的 `project.name`、时区、随机种子和默认数据源 profile。
3. 参考 `docs/project_readme_template.md` 重写新项目 README。
4. 删除不适用于当前项目的示例 SQL、占位说明或空目录说明。
5. 保留或初始化 `docs/framework_issue_log.md`，用于记录项目使用过程中的问题和框架改进建议。
6. 如调整 `scripts/` 下的可执行脚本，同步更新 `docs/script_catalog.md`。

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

本文档不重复维护检查清单。提交前至少应确认已按该文档完成项目完成检查、最低交付标准检查、禁止事项检查和交付前审计流程。
