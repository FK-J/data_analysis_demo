# 数据分析项目模板

这是一个可复用的数据分析项目模板，用于快速创建可复现、可审计、可交付的数据分析项目。

模板的核心约定是：

- `notebooks/main_analysis.ipynb` 是唯一主分析入口。
- `configs/` 管理项目参数和数据源配置。
- `sql/` 保存可复用 SQL。
- `src/` 保存可复用 Python 逻辑。
- `reports/` 保存图表、结果表和最终交付物。
- `tests/` 保存关键函数、指标逻辑和数据校验测试。
- `logs/` 保存运行日志和审计信息。

## 1. 如何使用本模板

创建新分析项目时，建议按以下顺序处理：

1. 复制本模板到新项目目录。
2. 阅读 `agent.md` 和 `docs/` 下的项目规范。
3. 参考 `docs/project_readme_template.md` 重写新项目的 `README.md`。
4. 按需复制 `configs/database.example.yaml` 为 `configs/database.yaml`。
5. 在 `configs/analysis_config.yaml` 中设置项目名称、时间范围、随机种子和数据源 profile。
6. 在 `notebooks/main_analysis.ipynb` 中填写业务背景、数据说明、分析过程和结论。
7. 将复杂 SQL 放入 `sql/`，复杂 Python 逻辑放入 `src/`。
8. 将关键结果导出到 `reports/`，并在 Notebook 中记录输出路径。
9. 交付前按 `docs/08_reproducibility_audit_checklists.md` 完成审计。

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

Notebook 应该作为流程编排和结论展示入口，不应堆放大量复杂逻辑。

建议：

- 复杂 SQL 放到 `sql/`。
- 复杂 Python 函数放到 `src/`。
- 关键图表和结果表导出到 `reports/`。
- 提交前清理 Notebook 临时输出，避免产生无意义的大 diff。

可以使用 Jupyter 自带的 `Clear All Outputs`，也可以在项目中按需引入 `nbstripout` 或 `jupytext`。

## 6. 敏感信息规则

禁止提交：

- `.env`
- `configs/database.yaml`
- 真实数据库账号、密码、host
- token、密钥、私有连接串
- 未脱敏的敏感明细数据
- 大型原始数据文件

如果必须保留示例数据，必须确认数据已经脱敏，且体积适合进入 Git。

## 7. 目录说明

详细目录职责见：

```text
docs/02_project_structure.md
```

数据库连接和 SQL 执行规范见：

```text
docs/04_python_sql_database_standard.md
```
