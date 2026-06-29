# 数据分析项目 Agent 规范目录

本文档是数据分析项目的规范入口和文档目录。具体执行细节不在本文档展开，必须阅读 `docs/` 目录下的独立规范文档。

## 1. 使用方式

后续任何数据分析项目开始前，Agent 必须先阅读本文档，再按项目需要阅读对应分册。

默认执行原则：

- 在正式读取数据、编写 SQL、建模或制图之前，必须先与用户确认业务分析框架。
- 业务分析框架必须保存为 `docs/analysis_framework.md`，可基于 `docs/analysis_framework_template.md` 创建。
- 在分析执行前，应同步确认最终报告呈现结构，并保存为 `reports/final/final_report_structure.md`。
- 后续用户提出新的分析需求时，必须先判断并同步更新 `docs/analysis_framework.md`，再修改 Notebook、SQL、Python 或报告。
- 必须使用 `notebooks/main_analysis.ipynb` 作为唯一主分析入口。
- 可以使用 Python 脚本封装复杂逻辑，但必须由主 Notebook 调用。
- 可以使用 SQL 文件沉淀抽取、转换和校验逻辑，但必须由 Python 在主 Notebook 中执行。
- 可直接执行脚本的功能、输入、输出和使用规范必须记录在 `docs/script_catalog.md`。
- 新增、删除、重命名或修改 `scripts/` 下的脚本时，必须同步更新 `docs/script_catalog.md`。
- 可以通过 Python 直接连接数据库，但禁止硬编码真实账号、密码、密钥或生产库敏感配置。
- Notebook 每个主要步骤必须写清楚目的、上游依赖、输入文件/对象、输出文件/对象、是否可缓存和调试提示。
- 所有关键结果或结论必须可以追溯到数据、SQL、Python 脚本或 Notebook cell。
- 最终报告必须通过 `scripts/generate_final_report.py` 生成，默认只呈现结果；除非用户明确要求，不生成洞察或业务解读。

核心目标：

> 每个项目必须先形成 `docs/analysis_framework.md` 和 `reports/final/final_report_structure.md`，再通过 `notebooks/main_analysis.ipynb` 从上到下完整复现，并最终由 `scripts/generate_final_report.py` 生成结果呈现型报告。

## 2. 规范文档目录

| 文档 | 用途 | 必读场景 |
| --- | --- | --- |
| [01_overview_and_principles.md](docs/01_overview_and_principles.md) | 项目适用范围、规范用语、总体工作原则、Agent 行为原则 | 所有项目必读 |
| [02_project_structure.md](docs/02_project_structure.md) | 项目目录结构、目录职责、文件命名、版本管理 | 所有项目必读 |
| [03_main_notebook_standard.md](docs/03_main_notebook_standard.md) | 主 Notebook 定位、章节结构、备注规范、执行规范、骨架模板 | 所有项目必读 |
| [04_python_sql_database_standard.md](docs/04_python_sql_database_standard.md) | Python 脚本规范、数据库连接、SQL 文件与执行规范 | 涉及 Python、SQL 或数据库时必读 |
| [05_data_management_quality_cleaning.md](docs/05_data_management_quality_cleaning.md) | 数据分层、原始数据保护、敏感数据、质量检查、清洗转换 | 所有项目必读 |
| [06_analysis_modeling_standard.md](docs/06_analysis_modeling_standard.md) | 探索性分析、业务分析、统计分析、机器学习建模规范 | 涉及分析或建模时必读 |
| [07_visualization_reporting_delivery.md](docs/07_visualization_reporting_delivery.md) | 可视化、报告、结论表达、最终交付规范 | 所有交付型项目必读 |
| [08_reproducibility_audit_checklists.md](docs/08_reproducibility_audit_checklists.md) | 复现、日志、测试、审计、完成检查清单、禁止事项 | 项目完成前必读 |
| [script_catalog.md](docs/script_catalog.md) | 可执行脚本功能目录、命令示例、输入输出和安全注意事项 | 需要运行、新增或修改脚本时必读 |
| [analysis_framework_template.md](docs/analysis_framework_template.md) | 业务分析框架模板，先确认业务拆解、分析路径和分析边界 | 新项目启动时必用 |
| [final_report_structure_template.md](docs/final_report_structure_template.md) | 最终报告呈现结构模板，先确认报告结构和每节分析逻辑 | 新项目启动时必用 |
| [report_inputs_template.yaml](docs/report_inputs_template.yaml) | 报告生成脚本输入模板 | 导出报告输入素材时使用 |
| [final_analysis_report_template.md](docs/final_analysis_report_template.md) | 结果呈现型报告结构说明 | 输出最终报告时使用 |

## 3. 推荐阅读顺序

新项目建议按以下顺序阅读规范：

```text
agent.md
→ docs/01_overview_and_principles.md
→ docs/02_project_structure.md
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

默认项目形态如下：

```text
project/
  agent.md
  README.md
  .env.example
  docs/
    analysis_framework.md
  configs/
  data/
  sql/
  src/
  notebooks/
    main_analysis.ipynb
  reports/
  tests/
  logs/
```

详细目录职责见：[02_project_structure.md](docs/02_project_structure.md)。

## 5. 最低执行要求

即使是小型数据分析项目，也必须满足以下最低要求：

- 有清晰的业务问题和分析目标。
- 有已确认的 `docs/analysis_framework.md`。
- 有已确认的 `reports/final/final_report_structure.md`。
- 有 `notebooks/main_analysis.ipynb`。
- 主 Notebook 可以从上到下顺序执行。
- 主 Notebook 每个主要步骤都有 Markdown 备注。
- 数据来源、时间范围、统计粒度和核心指标口径已说明。
- 数据质量检查已完成。
- SQL 文件保存在 `sql/`，并由主 Notebook 通过 Python 执行。
- 复杂 Python 逻辑保存在 `src/`，并由主 Notebook 调用。
- 如存在可直接执行脚本，`docs/script_catalog.md` 已记录脚本功能、输入、输出和运行方式。
- 关键图表和结果表已导出到 `reports/`。
- 最终报告由脚本生成，默认只呈现结果、图表、表格、口径和限制。
- 不包含真实数据库密码、密钥、token 或敏感明细数据。

完整检查清单见：[08_reproducibility_audit_checklists.md](docs/08_reproducibility_audit_checklists.md)。

## 6. Agent 执行提醒

后续 Agent 在项目中必须保持以下工作方式：

- 先明确问题，再读取和处理数据。
- 先和用户讨论业务分析框架，再进入具体取数、分析和建模。
- 先确认最终报告呈现结构，再导出报告素材和生成报告。
- 先建立可复现流程，再优化分析细节。
- 先完成数据质量检查，再输出业务结果或结论。
- 先判断是否需要统计分析或机器学习，再选择方法。
- 运行、新增或修改可直接执行脚本前，先查看并维护 `docs/script_catalog.md`。
- 如用户明确要求生成洞察或建议，必须区分事实、推断、建议和局限性。
- 不因展示技术而使用不必要的复杂模型。
- 不把相关性直接解释为因果性。
- 不把 Notebook 当作临时代码草稿，而应作为最终可审阅的分析入口。

---

本文档只作为规范目录和项目入口使用。所有细节以 `docs/` 目录中的分册规范为准。
