# 数据分析项目 Agent 规范目录

本文档是数据分析项目的规范入口和文档目录。具体执行细节不在本文档展开，必须阅读 `docs/` 目录下的独立规范文档。

## 1. 使用方式

后续任何数据分析项目开始前，Agent 必须先阅读本文档，再按项目需要阅读对应分册。

默认执行原则：

- 开始前必须读取并校验 `project.yaml`；它决定项目模式、数据源、可选 Notebook 章节和预期交付物。
- 在正式读取数据、编写 SQL、建模或制图之前，必须先与用户确认业务分析框架。
- 业务分析框架必须保存为 `docs/analysis_framework.md`，可基于 `docs/analysis_framework_template.md` 创建。
- 在分析执行前，应同步确认最终报告呈现结构，并保存为 `reports/final/final_report_structure.md`。
- 后续用户提出新的分析需求时，必须先在 `docs/change_execution_log.md` 登记需求、等级、验收标准和影响范围。
- 只有业务契约发生变化时才更新 `docs/analysis_framework.md`；修复实现以符合原口径时不改写业务框架。
- 修改后必须从最早受影响环节运行到最远受影响产物，不得把“文件已修改”作为完成标准。
- L3 变更、无法确认缓存有效性或准备正式交付时，必须从头到尾顺序运行主 Notebook 并重新生成最终报告。
- 只有框架、模板、工具或流程本身存在缺陷、卡点或重复绕行时，才记录到 `docs/framework_issue_log.md`，并关联 `change_id`。
- 必须使用 `notebooks/main_analysis.ipynb` 作为唯一主分析入口。
- Notebook 必须基于 `templates/notebook_sections.yaml` 和 `project.yaml` 生成；数据库、统计和建模章节只在配置启用时出现。
- 可以使用 Python 脚本封装复杂逻辑，但必须由主 Notebook 调用。
- 可以使用 SQL 文件沉淀抽取、转换和校验逻辑，但必须由 Python 在主 Notebook 中执行。
- 可直接执行脚本的功能、输入、输出和使用规范必须记录在 `docs/script_catalog.md`。
- 新增、删除、重命名或修改 `scripts/` 下的脚本时，必须同步更新 `docs/script_catalog.md`。
- 可以通过 Python 直接连接数据库，但禁止硬编码真实账号、密码、密钥或生产库敏感配置。
- Notebook 每个主要步骤必须写清楚目的、上游依赖、输入文件/对象、输出文件/对象、是否可缓存和调试提示。
- 所有关键结果或结论必须可以追溯到数据、SQL、Python 脚本或 Notebook cell。
- 最终报告必须通过 `scripts/generate_final_report.py` 生成，默认只呈现结果；除非用户明确要求，不生成洞察或业务解读。
- 交付前必须依次通过 `scripts/validate_project.py`、`scripts/run_notebook.py` 和 `scripts/audit_project.py`。
- 自动化脚本只用于生成与验收，不得绕过主 Notebook 形成第二套分析流程。

核心目标：

> 每个项目必须先形成 `docs/analysis_framework.md` 和 `reports/final/final_report_structure.md`，再通过 `notebooks/main_analysis.ipynb` 从上到下完整复现，并最终由 `scripts/generate_final_report.py` 生成结果呈现型报告。

后续修改必须按 `docs/09_change_management_standard.md` 完成登记、影响判断、重跑、校验和产物同步。

## 2. 文档职责总览

文档职责按“入口、工作流、领域规范、模板、检查清单”分层。遇到重复信息时，以表中的“核心作用”为准。

| 文档 | 核心作用 | 不负责 |
| --- | --- | --- |
| [README.md](README.md) | 项目入口和快速导航，说明最少必读文件、常用命令和安全底线。 | 不展开完整工作流和细则。 |
| [agent.md](agent.md) | Agent 执行入口，说明默认原则、文档职责和最低交付要求。 | 不替代各分册的详细规范。 |
| [template_usage.md](docs/template_usage.md) | 工作流主文档，沉淀新做分析、中途修改需求和贯穿式问题记录流程。 | 不写具体项目的业务内容。 |
| [framework_issue_log.md](docs/framework_issue_log.md) | 记录框架、模板、工具或流程缺陷、根因和改进建议。 | 不记录普通业务需求、数据质量问题或变更执行状态。 |
| [01_overview_and_principles.md](docs/01_overview_and_principles.md) | 总原则，定义业务框架先行、可复现、口径、安全和方法边界。 | 不维护逐步操作清单。 |
| [02_project_structure.md](docs/02_project_structure.md) | 目录职责、文件命名、版本管理和 README 内容要求。 | 不规定分析方法细节。 |
| [03_main_notebook_standard.md](docs/03_main_notebook_standard.md) | 主 Notebook 的章节、备注格式、局部调试和正式运行要求。 | 不定义具体业务问题。 |
| [04_python_sql_database_standard.md](docs/04_python_sql_database_standard.md) | Python 模块、数据库连接和 SQL 文件/执行规范。 | 不管理业务报告结构。 |
| [05_data_management_quality_cleaning.md](docs/05_data_management_quality_cleaning.md) | 数据分层、数据理解、质量检查、清洗和敏感数据处理。 | 不规定统计或建模方法。 |
| [06_analysis_modeling_standard.md](docs/06_analysis_modeling_standard.md) | EDA、业务分析、指标分析、统计分析和建模方法边界。 | 不规定报告文件格式。 |
| [07_visualization_reporting_delivery.md](docs/07_visualization_reporting_delivery.md) | 图表、结果表、最终报告、可选洞察和交付表达规范。 | 不维护项目审计清单。 |
| [08_reproducibility_audit_checklists.md](docs/08_reproducibility_audit_checklists.md) | 复现、日志、测试、审计和交付前检查清单。 | 不描述新项目启动流程。 |
| [09_change_management_standard.md](docs/09_change_management_standard.md) | 后续修改的唯一分级、影响、重跑和完成规范。 | 不承载具体业务契约。 |
| [change_execution_log.md](docs/change_execution_log.md) | 每次修改的需求、执行范围、完成情况和风险记录。 | 不替代业务框架、报告结构或问题根因记录。 |
| [script_catalog.md](docs/script_catalog.md) | 可直接执行脚本的功能、输入、输出、命令示例和安全注意事项。 | 不记录 `src/` 下只能被 import 的辅助模块。 |
| [analysis_framework_template.md](docs/analysis_framework_template.md) | 具体项目业务分析框架模板，承载业务问题、假设、边界和需求变更记录。 | 不替代最终报告结构。 |
| [final_report_structure_template.md](docs/final_report_structure_template.md) | 具体项目最终报告结构模板，分析前确认章节、逻辑、图表和表格计划。 | 不承载最终分析结果。 |
| [report_inputs_template.yaml](docs/report_inputs_template.yaml) | 报告生成脚本的结构化输入模板。 | 不定义业务分析框架。 |
| [final_analysis_report_template.md](docs/final_analysis_report_template.md) | 最终报告成品的结构说明，指导脚本生成 `final_analysis_report.md`。 | 不作为项目分析前的报告方案确认稿。 |
| [project_readme_template.md](docs/project_readme_template.md) | 具体项目 README 模板。 | 不作为本模板仓库的入口说明。 |

## 3. 推荐阅读顺序

新项目建议按以下顺序阅读规范：

```text
agent.md
→ docs/template_usage.md
→ docs/09_change_management_standard.md
→ docs/01_overview_and_principles.md
→ docs/02_project_structure.md
→ docs/framework_issue_log.md
→ docs/analysis_framework_template.md
→ docs/final_report_structure_template.md
→ docs/03_main_notebook_standard.md
→ docs/04_python_sql_database_standard.md
→ docs/script_catalog.md
→ docs/05_data_management_quality_cleaning.md
→ docs/06_analysis_modeling_standard.md
→ docs/07_visualization_reporting_delivery.md
→ docs/08_reproducibility_audit_checklists.md
```

如果项目只做本地文件分析，不连接数据库，也必须阅读 `04_python_sql_database_standard.md` 中的 Python 脚本规范；数据库和 SQL 部分可以标注“不适用”。

## 4. 标准项目形态

标准目录结构、目录职责、文件命名和版本管理规则统一维护在 [02_project_structure.md](docs/02_project_structure.md)。项目根目录必须包含 `project.yaml`、`.harness/`、`schemas/` 和 `templates/`，本文档不重复展开目录树。

## 5. 最低执行要求

即使是小型数据分析项目，也必须满足以下最低要求：

- 有清晰的业务问题和分析目标。
- 有当前修改对应的 `docs/change_execution_log.md` 记录。
- 有已确认的 `docs/analysis_framework.md`。
- 有已确认的 `reports/final/final_report_structure.md`。
- 有 `notebooks/main_analysis.ipynb`。
- `project.yaml` 已通过 Schema 校验，Notebook 章节与配置一致。
- 主 Notebook 可以从上到下顺序执行。
- 主 Notebook 每个主要步骤都有 Markdown 备注。
- 数据来源、时间范围、统计粒度和核心指标口径已说明。
- 数据质量检查已完成。
- SQL 文件保存在 `sql/`，并由主 Notebook 通过 Python 执行。
- 复杂 Python 逻辑保存在 `src/`，并由主 Notebook 调用。
- 如存在可直接执行脚本，`docs/script_catalog.md` 已记录脚本功能、输入、输出和运行方式。
- 已发现的框架、模板、工具或流程缺陷已记录到 `docs/framework_issue_log.md` 并关联 `change_id`。
- 变更已运行到最远受影响产物，检查项和剩余风险已记录。
- 关键图表和结果表已导出到 `reports/`。
- 最终报告由脚本生成，默认只呈现结果、图表、表格、口径和限制。
- 不包含真实数据库密码、密钥、token 或敏感明细数据。
- 最近一次无界面 Notebook 执行通过，交付审计没有失败项。

完整检查清单见：[08_reproducibility_audit_checklists.md](docs/08_reproducibility_audit_checklists.md)。

## 6. Agent 执行提醒

后续 Agent 在项目中必须保持以下工作方式：

- 先明确问题，再读取和处理数据。
- 先和用户讨论业务分析框架，再进入具体取数、分析和建模。
- 先确认最终报告呈现结构，再导出报告素材和生成报告。
- 先建立可复现流程，再优化分析细节。
- 先完成数据质量检查，再输出业务结果或结论。
- 先判断是否需要统计分析或机器学习，再选择方法。
- 修改前先更新变更执行日志，确认等级、验收标准、影响范围和重跑起点。
- 修改后运行到最远受影响产物；正式交付前完整运行主 Notebook 并重新生成报告。
- 运行、新增或修改可直接执行脚本前，先查看并维护 `docs/script_catalog.md`。
- 遇到框架、模板、工具或流程卡点、临时绕行时，及时维护 `docs/framework_issue_log.md`。
- 如用户明确要求生成洞察或建议，必须区分事实、推断、建议和局限性。
- 不因展示技术而使用不必要的复杂模型。
- 不把相关性直接解释为因果性。
- 不把 Notebook 当作临时代码草稿，而应作为最终可审阅的分析入口。

---

本文档只作为规范目录和项目入口使用。所有细节以 `docs/` 目录中的分册规范为准。
