# 02. 项目目录与文件组织规范

## 1. 标准项目目录结构

每个项目应该采用以下目录结构：

```text
project/
  agent.md
  README.md
  .env.example
  docs/
    analysis_framework.md
    analysis_framework_template.md
    final_report_structure_template.md
    final_analysis_report_template.md
    report_inputs_template.yaml
  configs/
    database.example.yaml
    analysis_config.yaml
  data/
    raw/
    interim/
    processed/
    external/
  sql/
    extract/
    transform/
    validation/
  src/
    db/
      connection.py
      sql_runner.py
    io/
    quality/
    cleaning/
    features/
    analysis/
    stats/
    modeling/
    visualization/
    reporting/
  notebooks/
    main_analysis.ipynb
  scripts/
    generate_final_report.py
  reports/
    figures/
    tables/
    final/
  tests/
  logs/
```

小项目可以精简目录，但不得改变核心逻辑：原始数据、SQL、Python 脚本、主 Notebook、结果输出必须有清晰边界。

## 2. 目录职责

- `agent.md`：项目规范入口和文档目录。
- `docs/`：细节规范文档、业务分析框架和报告模板。
- `docs/analysis_framework.md`：具体项目的业务分析框架，正式分析前必须与用户确认。
- `docs/analysis_framework_template.md`：业务分析框架模板。
- `docs/final_report_structure_template.md`：最终报告结构模板。
- `docs/final_analysis_report_template.md`：结果呈现型报告结构说明。
- `docs/report_inputs_template.yaml`：报告生成脚本输入模板。
- `README.md`：项目背景、运行方式、依赖说明和交付物说明。
- `.env.example`：环境变量示例，禁止包含真实账号、密码、密钥。
- `configs/`：配置文件目录，包括数据库连接示例、分析参数、日期范围等。
- `data/raw/`：原始数据目录，禁止手动修改。
- `data/interim/`：中间处理数据。
- `data/processed/`：最终分析数据。
- `data/external/`：外部补充数据。
- `sql/extract/`：数据抽取 SQL。
- `sql/transform/`：数据转换 SQL。
- `sql/validation/`：数据校验 SQL。
- `src/`：可复用 Python 脚本。
- `notebooks/main_analysis.ipynb`：唯一主分析 Notebook，必须完整执行全流程。
- `scripts/generate_final_report.py`：固定生成最终报告的脚本，默认只呈现结果。
- `reports/figures/`：图表文件。
- `reports/tables/`：结果表文件。
- `reports/final/`：最终报告结构、报告输入素材、最终报告和交付材料。
- `tests/`：关键函数、指标逻辑或数据校验测试。
- `logs/`：运行日志。

## 3. Notebook 数量规范

默认只允许保留一个主 Notebook：

```text
notebooks/main_analysis.ipynb
```

可以临时创建探索性 Notebook，但最终交付前必须清理或归档。最终项目的完整执行入口必须是 `notebooks/main_analysis.ipynb`。

禁止出现以下情况：

- 分析逻辑分散在多个 Notebook 中，且没有统一执行入口。
- 关键结果只存在于 Notebook 输出缓存中，没有导出文件。
- 主 Notebook 依赖手动复制粘贴其他 Notebook 的结果。

## 4. 文件命名规范

### 4.1 SQL 文件命名

```text
01_extract_orders.sql
02_extract_users.sql
03_transform_user_metrics.sql
04_validate_order_metrics.sql
```

命名原则：

- 使用数字前缀体现执行顺序。
- 使用英文小写和下划线。
- 文件名应体现用途。
- 抽取、转换、校验 SQL 应分别放入对应目录。

### 4.2 Python 文件命名

```text
connection.py
sql_runner.py
data_quality.py
cleaning_rules.py
feature_builder.py
business_metrics.py
stat_tests.py
model_training.py
plotting.py
export_report.py
```

命名原则：

- 文件名表达模块职责。
- 函数名表达业务含义或处理目的。
- 不使用无意义名称，如 `utils2.py`、`test_new.py`、`final_final.py`。

### 4.3 输出文件命名

```text
data_quality_summary.csv
business_metrics_summary.csv
statistical_test_results.csv
model_performance_summary.csv
fig_01_metric_trend.png
fig_02_segment_comparison.png
fig_03_model_performance.png
final_analysis_report.md
final_report_structure.md
report_inputs.yaml
```

命名原则：

- 结果表使用清晰业务名称。
- 图表建议使用 `fig_序号_主题.png`。
- 最终报告结构建议命名为 `final_report_structure.md`，统一保存到 `reports/final/`。
- 报告生成输入建议命名为 `report_inputs.yaml`，统一保存到 `reports/final/`。
- 最终报告建议命名为 `final_analysis_report.md`，由 `scripts/generate_final_report.py` 生成并保存到 `reports/final/`。

## 5. README 要求

`README.md` 应该包含：

- 项目名称。
- 项目背景。
- 业务问题。
- 业务分析框架文档位置。
- 最终报告结构文件位置。
- 目录结构说明。
- 环境依赖。
- 数据来源说明。
- 数据库连接配置方式。
- 如何运行 `notebooks/main_analysis.ipynb`。
- 如何运行 `scripts/generate_final_report.py`。
- 输出文件位置。
- 注意事项。

具体项目的业务分析框架必须保存为：

```text
docs/analysis_framework.md
```

具体项目的最终报告结构必须保存为：

```text
reports/final/final_report_structure.md
```

`reports/final/report_inputs.yaml` 是报告生成输入素材，默认可不提交到 Git。

## 6. 配置文件要求

配置文件应该放在 `configs/` 中。

常见配置包括：

- 分析时间范围。
- 输出路径。
- 随机种子。
- 业务参数。
- 数据库连接示例。
- 是否使用缓存。
- 是否只读执行 SQL。

禁止在配置文件中提交真实数据库密码、token、密钥或私有连接信息。

## 7. 版本管理规范

项目应该纳入版本管理。

必须避免提交：

- `.env`。
- 数据库真实凭据。
- 大型原始数据。
- 敏感明细数据。
- 临时缓存文件。
- 无关 Notebook 检查点。
- 包含敏感结果或明细的 `reports/final/report_inputs.yaml`。

建议 `.gitignore` 包含：

```text
.env
.ipynb_checkpoints/
__pycache__/
*.pyc
data/raw/
data/interim/
data/processed/
logs/
```

如果项目需要提交最终报告结构和最终报告，可以在 `.gitignore` 中保留：

```text
!reports/final/final_report_structure.md
!reports/final/final_analysis_report.md
```

如果项目需要保留小型示例数据，必须确认数据已脱敏。

## 8. 最低目录要求

如果项目非常小，至少必须保留：

```text
project/
  agent.md
  README.md
  docs/
    analysis_framework.md
  data/
  sql/
  src/
  notebooks/
    main_analysis.ipynb
  reports/
```

任何不使用的目录，可以在 README 或 Notebook 中说明“不适用”。
