# 模板使用说明

本文档说明如何把本仓库作为新数据分析项目模板使用。

## 1. 初始化新项目

1. 复制本模板到新项目目录。
2. 修改 `configs/analysis_config.yaml` 中的 `project.name`。
3. 参考 `docs/project_readme_template.md` 重写新项目 README。
4. 打开 `notebooks/main_analysis.ipynb`，填写业务背景、分析目标、数据来源和输出要求。
5. 删除不适用于当前项目的示例 SQL 或占位说明。

## 2. 配置数据源

如果使用数据库：

1. 复制 `configs/database.example.yaml` 为 `configs/database.yaml`。
2. 选择或新增 `profiles` 下的数据源 profile。
3. 在 `configs/analysis_config.yaml` 中设置 `analysis.database_profile`。
4. 使用环境变量或 `.env` 保存敏感连接信息。

如果只使用本地文件：

1. 将原始数据放到 `data/raw/`，或将外部参考数据放到 `data/external/`。
2. 在 Notebook 中说明数据来源、时间范围、粒度和字段含义。
3. 不需要真实数据库配置时，在 Notebook 中标注数据库部分不适用。

## 3. 编写分析流程

主流程必须通过 `notebooks/main_analysis.ipynb` 从上到下复现。

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

## 4. 输出交付物

推荐输出路径：

```text
reports/figures/    图表
reports/tables/     结果表
reports/final/      最终报告或交付材料
logs/               运行日志和审计记录
```

关键结论不能只存在于 Notebook 输出缓存中，必须有可追溯的图表、结果表或报告文件。

## 5. 提交前检查

提交前至少确认：

- `notebooks/main_analysis.ipynb` 可以从上到下顺序运行。
- 关键 SQL 已保存到 `sql/`。
- 复杂 Python 逻辑已保存到 `src/`。
- 关键图表和结果表已导出到 `reports/`。
- README 已说明复现方式。
- 没有提交 `.env`、`configs/database.yaml` 或真实敏感数据。
- Notebook 临时输出已清理，或确认输出需要保留。

完整检查清单见：

```text
docs/08_reproducibility_audit_checklists.md
```
