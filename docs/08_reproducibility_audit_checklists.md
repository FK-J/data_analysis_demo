# 08. 复现、审计与检查清单

## 1. 复现规范

项目必须提供复现说明。

`README.md` 应该包含：

- 项目名称。
- 项目背景。
- 业务分析框架文档位置。
- 变更管理规范和 `docs/change_execution_log.md` 的位置与维护要求。
- 框架问题记录 `docs/framework_issue_log.md` 的位置和维护要求。
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

除分析师在 Jupyter 中交互检查外，还必须运行 `python scripts/run_notebook.py`。该命令使用干净内核从头执行主 Notebook，并保存：

```text
logs/runs/<run_id>/executed_main_analysis.ipynb
logs/runs/<run_id>/manifest.json
```

运行清单记录项目、Git commit、开始和结束时间、执行状态、预检结果、输出路径和错误摘要，用于失败定位和交付审计。

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

## 3. 框架问题与迭代记录规范

框架、模板、工具或流程本身出现的问题应该及时记录到：

```text
docs/framework_issue_log.md
```

需要记录的问题包括规范冲突、流程卡点、文档不足、脚本难用、Notebook 无法按规范复现和临时绕行方案。

普通业务需求和执行状态不在问题日志重复记录。问题处理应关联 Change ID，执行状态以 `docs/change_execution_log.md` 为准。

交付前只检查已发现的框架问题是否记录、分类和关联，不把问题记录延后到最后一次性补写。

## 4. 每次变更完成检查

所有受管变更必须遵循 `docs/09_change_management_standard.md`。

变更完成前必须确认：

- `docs/change_execution_log.md` 已填写等级、验收标准、影响范围、重跑起点和必达产物。
- 业务框架或报告结构变化已经同步。
- 已从最早受影响环节运行到最远受影响产物。
- 数据质量、指标口径、总计、筛选范围和新旧结果差异已按需检查。
- 图表、结果表、报告输入和最终报告已按影响范围更新。
- 不存在未说明的失败项或未完成项。

正式交付前还必须从头到尾顺序运行主 Notebook，并重新生成最终报告。

## 5. 测试与校验规范

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

项目结构和交付物检查必须使用：

```bash
python scripts/validate_project.py
python scripts/audit_project.py
```

前者检查配置 Schema、必需文件、Notebook 章节、占位内容、SQL 只读策略和敏感文件；后者进一步检查图表、结果表、报告输入、最终报告及最近一次无界面执行证据。

## 6. 项目完成检查清单

每个项目完成前，必须逐项检查：

- [ ] 已与用户确认业务分析框架。
- [ ] `docs/analysis_framework.md` 已创建并保存。
- [ ] 已与用户确认最终报告呈现结构。
- [ ] `reports/final/final_report_structure.md` 已创建并保存。
- [ ] `docs/framework_issue_log.md` 已保留或创建。
- [ ] 当前修改已记录到 `docs/change_execution_log.md`。
- [ ] 等级、验收标准、影响范围、重跑起点和必达产物已确认。
- [ ] 核心业务问题、业务拆解框架、分析路径和分析边界已说明。
- [ ] 业务契约发生变化时，已同步到 `docs/analysis_framework.md` 并关联 `change_id`。
- [ ] 框架、模板、工具或流程缺陷已记录到 `docs/framework_issue_log.md` 并关联 `change_id`。
- [ ] 框架通用问题已写明修改建议、影响范围和关联文件。
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
- [ ] 当前修改已运行到最远受影响产物，相关检查和剩余风险已记录。
- [ ] `project.yaml` 已通过 Schema 校验，Notebook 章节与配置一致。
- [ ] 最近一次 `scripts/run_notebook.py` 执行成功并保存运行清单。
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
- [ ] `scripts/audit_project.py` 没有失败项。

## 7. 最低交付标准

如果项目时间紧张，至少必须满足以下最低标准：

- 有 `notebooks/main_analysis.ipynb`。
- 有已确认的 `docs/analysis_framework.md`。
- 有 `docs/framework_issue_log.md`，且已记录框架、模板、工具或流程缺陷，或明确无新增问题。
- 有当前修改的变更执行记录，且所有必做项已完成。
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

## 8. 禁止事项汇总

以下行为在项目中禁止出现：

- 未明确业务问题就开始分析。
- 未确认业务分析框架就开始取数、建模或制图。
- 未确认最终报告结构就开始执行分析。
- 业务契约发生变化后，未同步更新 `docs/analysis_framework.md` 或未关联 `change_id`。
- 受管修改未先更新变更执行日志，或只修改局部文件而未运行下游流程。
- 框架、模板、工具或流程缺陷发生后，未记录到 `docs/framework_issue_log.md`。
- 发现框架通用问题后，未判断影响范围或未形成修改建议。
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

## 9. 交付前审计流程

交付前必须按以下顺序审计：

```text
1. 检查 docs/analysis_framework.md 是否存在且已确认
2. 检查 reports/final/final_report_structure.md 是否存在且已确认
3. 检查 docs/change_execution_log.md 中的等级、影响范围、完成情况和风险
4. 检查业务框架和报告结构变化是否同步
5. 运行 scripts/validate_project.py
6. 运行 scripts/run_notebook.py，在干净内核中从头执行主 Notebook
7. 检查是否有报错，数据质量结果是否通过
8. 检查 SQL 文件和 Python 脚本是否由 Notebook 调用
9. 检查 docs/script_catalog.md 是否与 scripts/ 目录一致
10. 检查图表、结果表和 report_inputs.yaml 是否更新
11. 运行 scripts/generate_final_report.py
12. 检查最终报告的结构、占位内容、洞察开关和敏感信息
13. 运行 scripts/audit_project.py 并确认没有失败项
14. 将变更执行记录更新为已完成或说明阻塞项
```

## 10. 审计结果记录

项目完成时，建议在 Notebook 最后一节记录：

```markdown
## 项目完成检查

- 业务分析框架确认状态：
- 最终报告结构确认状态：
- 使用问题记录状态：
- 框架通用问题处理状态：
- 分析框架变更同步状态：
- Change ID：
- 变更执行状态：
- 重跑起点和终点：
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
