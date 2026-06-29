# 08. 复现、审计与检查清单

## 1. 复现规范

项目必须提供复现说明。

`README.md` 应该包含：

- 项目名称。
- 项目背景。
- 业务分析框架文档位置。
- 最终报告结构文件位置。
- 目录结构说明。
- 环境依赖。
- 数据来源说明。
- 数据库连接配置方式。
- 如何运行 `notebooks/main_analysis.ipynb`。
- 脚本功能目录 `docs/script_catalog.md` 的位置和维护要求。
- 输出文件位置。
- 注意事项。

建议记录 Python 依赖：

```text
requirements.txt
```

或：

```text
environment.yml
```

Notebook 执行完成后，必须确认：

- 已引用并遵循 `docs/analysis_framework.md`。
- 已引用并遵循 `reports/final/final_report_structure.md`。
- 所有 cell 已按顺序运行。
- 没有报错。
- 输出文件已生成。
- 图表和结果表路径正确。
- 最终报告结果与输出文件一致。

## 2. 日志与审计规范

关键执行过程应该记录日志。

建议记录：

- SQL 文件执行时间。
- SQL 返回行数。
- 数据清洗前后行数。
- 缺失值处理数量。
- 异常值处理数量。
- 模型训练参数。
- 模型评估结果。
- 输出文件路径。

日志可以保存到：

```text
logs/
```

禁止将数据库密码、token、密钥或敏感明细数据写入日志。

## 3. 测试与校验规范

关键逻辑必须进行校验。

应该测试或校验：

- 指标计算函数。
- 数据清洗函数。
- 特征工程函数。
- SQL 查询结果行数。
- 主键唯一性。
- 多表 join 后行数变化。
- 关键汇总指标是否在合理范围。
- 模型评估函数。

简单项目可以在 Notebook 中完成校验。复杂项目应该在 `tests/` 目录中编写测试。

## 4. 项目完成检查清单

每个项目完成前，必须逐项检查：

- [ ] 已与用户确认业务分析框架。
- [ ] `docs/analysis_framework.md` 已创建并保存。
- [ ] 已与用户确认最终报告呈现结构。
- [ ] `reports/final/final_report_structure.md` 已创建并保存。
- [ ] 核心业务问题、业务拆解框架、分析路径和分析边界已说明。
- [ ] 新增或变更的分析需求已同步到 `docs/analysis_framework.md`。
- [ ] 分析目标已明确。
- [ ] 决策场景已明确。
- [ ] 数据源已说明。
- [ ] 数据表和字段含义已说明。
- [ ] 数据粒度已说明。
- [ ] 时间范围已说明。
- [ ] 核心指标口径已定义。
- [ ] 数据库连接方式已说明。
- [ ] SQL 文件已保存到 `sql/`。
- [ ] SQL 文件包含头部说明。
- [ ] Notebook 已调用 SQL 文件，而非只手动复制结果。
- [ ] 可直接执行脚本已记录在 `docs/script_catalog.md`。
- [ ] 新增、删除、重命名或修改脚本后，`docs/script_catalog.md` 已同步更新。
- [ ] 数据质量检查已完成。
- [ ] 缺失值、重复值、异常值处理方式已说明。
- [ ] 清洗前后数据量变化已记录。
- [ ] Python 复杂逻辑已封装到 `src/`。
- [ ] 主 Notebook 可以从上到下完整运行。
- [ ] 每个主要 Notebook 步骤都有 Markdown 备注。
- [ ] 关键图表已导出到 `reports/figures/`。
- [ ] 关键结果表已导出到 `reports/tables/`。
- [ ] `reports/final/report_inputs.yaml` 已生成。
- [ ] 已运行 `scripts/generate_final_report.py`。
- [ ] 最终报告已保存到 `reports/final/final_analysis_report.md`。
- [ ] 最终报告按汇总结果和业务问题组织，而不是按代码顺序组织。
- [ ] 报告结果能追溯到 `docs/analysis_framework.md` 中的业务问题。
- [ ] 默认未生成大模型洞察，除非用户明确要求。
- [ ] 业务分析结果有数据支撑。
- [ ] 统计分析说明了方法、假设和局限。
- [ ] 机器学习建模说明了标签、特征、切分方式和评估指标。
- [ ] 没有把相关性直接解释为因果性。
- [ ] 已说明局限性和风险。
- [ ] 如包含洞察或建议，已确认用户明确要求并说明依据。
- [ ] 没有提交真实数据库凭据。
- [ ] 没有泄露敏感数据。
- [ ] README 已说明复现方式。

## 5. 最低交付标准

如果项目时间紧张，至少必须满足以下最低标准：

- 有 `notebooks/main_analysis.ipynb`。
- 有已确认的 `docs/analysis_framework.md`。
- 有已确认的 `reports/final/final_report_structure.md`。
- Notebook 可以顺序执行。
- Notebook 每个主要步骤有备注。
- 数据来源和指标口径已说明。
- 数据质量检查已完成。
- SQL 文件保存在 `sql/`，并由 Notebook 通过 Python 执行。
- 复杂 Python 逻辑保存在 `src/`，并由 Notebook 调用。
- 可直接执行脚本已记录在 `docs/script_catalog.md`，且脚本变更已同步更新该文档。
- 关键图表和结果表已导出到 `reports/`。
- `reports/final/report_inputs.yaml` 已生成。
- 最终报告由 `scripts/generate_final_report.py` 生成。
- 不包含真实数据库密码、密钥或敏感明细数据。

## 6. 禁止事项汇总

以下行为在项目中禁止出现：

- 未明确业务问题就开始分析。
- 未确认业务分析框架就开始取数、建模或制图。
- 未确认最终报告结构就开始执行分析。
- 用户新增分析需求后，未同步更新 `docs/analysis_framework.md`。
- 未进行数据质量检查就输出结果。
- 修改 `data/raw/` 原始数据。
- 静默删除、填补或过滤数据。
- 未说明口径就输出核心指标。
- 把相关性直接表述为因果性。
- 使用无法复现的手动步骤。
- 只在脚本中完成分析，主 Notebook 无法复现。
- 新增、删除、重命名或修改可执行脚本后，未同步更新 `docs/script_catalog.md`。
- Notebook 中缺少步骤说明和备注。
- 在代码、Notebook、日志或配置中硬编码真实数据库密码。
- 提交真实 `.env` 文件。
- 提交敏感明细数据。
- 在未说明风险的情况下执行写库、删表、更新或覆盖操作。
- 为了展示技术而使用不必要的复杂模型。
- 只报告模型指标，不解释业务意义。
- 只交付代码、Notebook 或结果图表，不交付脚本生成的最终报告。
- 未经用户明确要求，生成大模型洞察或业务解读。

## 7. 交付前审计流程

交付前建议按以下顺序审计：

```text
1. 检查 docs/analysis_framework.md 是否存在且已确认
2. 检查 reports/final/final_report_structure.md 是否存在且已确认
3. 检查新增需求是否已同步到分析框架和报告结构
4. 从头运行 notebooks/main_analysis.ipynb
5. 检查是否有报错
6. 检查 SQL 文件是否存在且有头部说明
7. 检查 Python 脚本是否由 Notebook 调用
8. 检查 docs/script_catalog.md 是否覆盖可直接执行脚本，并与 scripts/ 目录一致
9. 检查数据质量结果是否展示
10. 检查图表和结果表是否落地
11. 检查 reports/final/report_inputs.yaml 是否生成
12. 运行 scripts/generate_final_report.py
13. 检查最终报告是否保存
14. 检查是否默认未生成大模型洞察
15. 检查是否泄露敏感信息
```

## 8. 审计结果记录

项目完成时，建议在 Notebook 最后一节记录：

```markdown
## 项目完成检查

- 业务分析框架确认状态：
- 最终报告结构确认状态：
- 分析框架变更同步状态：
- Notebook 顺序执行状态：
- 数据质量检查状态：
- SQL 文件检查状态：
- 脚本功能目录检查状态：
- 输出文件检查状态：
- 报告输入素材状态：
- 脚本生成最终报告状态：
- 敏感信息检查状态：
- 剩余风险：
- 下一步事项：
```

如果存在未完成项，必须说明原因和影响。
