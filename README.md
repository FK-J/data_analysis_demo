# 数据分析项目模板

这是一个可复用的数据分析项目模板，用于快速创建可复现、可审计、可交付的数据分析项目。

模板的核心约定是：

- `notebooks/main_analysis.ipynb` 是唯一主分析入口。
- `docs/analysis_framework.md` 是具体项目的业务分析框架文档，正式分析前必须先和用户确认。
- `reports/final/final_report_structure.md` 是最终报告呈现结构，正式分析前应同步确认。
- `configs/` 管理项目参数和数据源配置。
- `sql/` 保存可复用 SQL。
- `src/` 保存可复用 Python 逻辑。
- `docs/script_catalog.md` 记录可直接执行脚本的功能、输入、输出和使用规范。
- `scripts/generate_final_report.py` 固定生成最终报告，默认只呈现结果。
- `reports/` 保存图表、结果表和最终交付物。
- `tests/` 保存关键函数、指标逻辑和数据校验测试。
- `logs/` 保存运行日志和审计信息。

## 1. 如何使用本模板

创建新分析项目时，建议按以下顺序处理：

1. 复制本模板到新项目目录。
2. 阅读 `agent.md` 和 `docs/` 下的项目规范。
3. 先和用户讨论业务背景、决策目标、核心业务问题和业务拆解框架。
4. 复制 `docs/analysis_framework_template.md` 为 `docs/analysis_framework.md`，保存确认后的业务分析框架。
5. 复制 `docs/final_report_structure_template.md` 为 `reports/final/final_report_structure.md`，确认最终报告呈现结构和每节分析逻辑。
6. 参考 `docs/project_readme_template.md` 重写新项目的 `README.md`。
7. 按需复制 `configs/database.example.yaml` 为 `configs/database.yaml`。
8. 在 `configs/analysis_config.yaml` 中设置项目名称、时间范围、随机种子和数据源 profile。
9. 在 `notebooks/main_analysis.ipynb` 中基于 `docs/analysis_framework.md` 执行数据加载、质量检查、分析和导出。
10. 将复杂 SQL 放入 `sql/`，复杂 Python 逻辑放入 `src/`。
11. 如新增、删除或修改可直接执行脚本，同步更新 `docs/script_catalog.md`。
12. 将关键结果导出到 `reports/`，并生成 `reports/final/report_inputs.yaml`。
13. 运行 `scripts/generate_final_report.py` 生成最终报告。
14. 交付前按 `docs/08_reproducibility_audit_checklists.md` 完成审计。

详细模板使用流程见：

```text
docs/template_usage.md
```

## 2. 环境准备

建议使用独立 Python 环境：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

如果使用 Conda：

```bash
conda create -n data-analysis-demo python=3.11
conda activate data-analysis-demo
pip install -r requirements.txt
```

## 3. 主分析入口

主 Notebook 固定为：

```text
notebooks/main_analysis.ipynb
```

所有 SQL 执行、数据加载、清洗、分析、建模、验证和结果导出，都必须能通过该 Notebook 从上到下完整复现。

Notebook 不是业务框架的替代品。具体分析开始前，必须先建立：

```text
docs/analysis_framework.md
```

后续用户提出新的分析需求时，必须先判断是否需要更新该业务分析框架，再同步修改 Notebook、SQL、Python 逻辑和最终报告。

同时需要确认最终报告呈现结构：

```text
reports/final/final_report_structure.md
```

该文件应说明汇总结果和各业务问题章节的呈现顺序、具体分析逻辑、预期图表和预期结果表。

## 4. 数据源配置

如果项目需要数据库连接，请复制：

```text
configs/database.example.yaml
```

为：

```text
configs/database.yaml
```

然后在 `configs/database.yaml` 中填写真实连接信息。

`configs/database.yaml` 已被 `.gitignore` 忽略，禁止提交真实数据库账号、密码、host、token 或其他敏感配置。

数据库连接代码支持通过 profile 创建 SQLAlchemy engine。模板内置 MySQL 和 SQLite 示例，后续可以扩展 PostgreSQL、DuckDB 等数据源。

## 5. Notebook 与版本管理

Notebook 应该作为流程编排和结果展示入口，不应堆放大量复杂逻辑。

建议：

- 复杂 SQL 放到 `sql/`。
- 复杂 Python 函数放到 `src/`。
- 关键图表和结果表导出到 `reports/`。
- 提交前清理 Notebook 临时输出，避免产生无意义的大 diff。

可以使用 Jupyter 自带的 `Clear All Outputs`，也可以在项目中按需引入 `nbstripout` 或 `jupytext`。

## 6. 最终报告生成

最终报告应保存到：

```text
reports/final/
```

最终报告由脚本生成：

```bash
python scripts/generate_final_report.py
```

脚本默认读取：

```text
reports/final/report_inputs.yaml
```

并生成：

```text
reports/final/final_analysis_report.md
```

报告默认只呈现结果、图表、表格、口径和输出文件路径，不自动生成洞察或业务解读。

如需渲染已准备好的洞察内容，必须显式运行：

```bash
python scripts/generate_final_report.py --with-insights
```

报告结构和输入格式参考：

```text
docs/final_report_structure_template.md
docs/final_analysis_report_template.md
docs/report_inputs_template.yaml
```

## 7. 脚本功能目录

可直接执行脚本的功能、输入、输出、命令示例和安全注意事项记录在：

```text
docs/script_catalog.md
```

需要快速执行某个脚本时，应先查看该文档。新增、删除、重命名或修改 `scripts/` 下的脚本时，必须同步更新 `docs/script_catalog.md`。

## 8. 敏感信息规则

禁止提交：

- `.env`
- `configs/database.yaml`
- 真实数据库账号、密码、host
- token、密钥、私有连接串
- 未脱敏的敏感明细数据
- 大型原始数据文件

如果必须保留示例数据，必须确认数据已经脱敏，且体积适合进入 Git。

## 9. 目录说明

详细目录职责见：

```text
docs/02_project_structure.md
```

数据库连接和 SQL 执行规范见：

```text
docs/04_python_sql_database_standard.md
```
