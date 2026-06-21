# 模板使用说明

本文档说明如何把本仓库作为新数据分析项目模板使用。

## 1. 初始化新项目

1. 复制本模板到新项目目录。
2. 修改 `configs/analysis_config.yaml` 中的 `project.name`。
3. 先和用户讨论业务背景、决策目标、核心业务问题、业务拆解框架和分析边界。
4. 复制 `docs/analysis_framework_template.md` 为 `docs/analysis_framework.md`，保存确认后的业务分析框架。
5. 复制 `docs/final_report_structure_template.md` 为 `reports/final/final_report_structure.md`，确认最终报告结构和每节分析逻辑。
6. 参考 `docs/project_readme_template.md` 重写新项目 README。
7. 打开 `notebooks/main_analysis.ipynb`，基于 `docs/analysis_framework.md` 和 `reports/final/final_report_structure.md` 填写分析过程。
8. 删除不适用于当前项目的示例 SQL 或占位说明。

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

## 6. 输出交付物

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

## 7. 提交前检查

提交前至少确认：

- `docs/analysis_framework.md` 已创建并与用户确认。
- `reports/final/final_report_structure.md` 已创建并与用户确认。
- 新增或变更的分析需求已同步到 `docs/analysis_framework.md`。
- `notebooks/main_analysis.ipynb` 可以从上到下顺序运行。
- 关键 SQL 已保存到 `sql/`。
- 复杂 Python 逻辑已保存到 `src/`。
- 关键图表和结果表已导出到 `reports/`。
- `reports/final/report_inputs.yaml` 已生成。
- 已通过 `scripts/generate_final_report.py` 生成最终报告。
- README 已说明复现方式。
- 没有提交 `.env`、`configs/database.yaml` 或真实敏感数据。
- Notebook 临时输出已清理，或确认输出需要保留。

完整检查清单见：

```text
docs/08_reproducibility_audit_checklists.md
```
