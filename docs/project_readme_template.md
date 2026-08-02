# 项目名称

简要说明本数据分析项目要解决的问题，以及面向的业务场景。

## 1. 项目背景

- 业务背景：
- 决策场景：
- 核心问题：
- 预期交付物：

## 2. 业务分析框架

本项目的业务分析框架文档位于：

```text
docs/analysis_framework.md
```

正式取数、清洗、建模和制图前，必须先确认该文档。

如用户提出新的分析需求，应先更新 `docs/change_execution_log.md`；只有业务契约发生变化时才更新 `docs/analysis_framework.md`。

## 3. 变更管理与框架问题

本项目的变更管理规范和执行日志位于：

```text
docs/09_change_management_standard.md
docs/change_execution_log.md
```

影响业务契约、计算结果、正式产物或复现链路的修改必须先登记，并运行到最远受影响产物。

框架、模板、工具或流程缺陷记录在：

```text
docs/framework_issue_log.md
```

普通业务需求和执行状态不在问题日志重复记录。

## 4. 最终报告结构

本项目的最终报告结构位于：

```text
reports/final/final_report_structure.md
```

正式分析前，应先确认该文件，明确汇总结果和每个业务问题章节的呈现内容、分析逻辑、图表和表格清单。

最终报告由脚本生成：

```bash
python scripts/generate_final_report.py
```

正式交付前必须从头到尾顺序运行主 Notebook，再生成最终报告。

默认不生成大模型洞察或业务解读。若需要渲染已准备好的洞察内容，应显式运行：

```bash
python scripts/generate_final_report.py --with-insights
```

## 5. 数据来源

| 数据源 | 说明 | 时间范围 | 粒度 | 负责人 |
| --- | --- | --- | --- | --- |
| 待填写 | 待填写 | 待填写 | 待填写 | 待填写 |

如使用数据库，请说明 profile 名称，不要写真实账号、密码或 host。

## 6. 核心指标口径

| 指标 | 口径 | 粒度 | 备注 |
| --- | --- | --- | --- |
| 待填写 | 待填写 | 待填写 | 待填写 |

## 7. 项目结构

```text
project.yaml   项目类型、模块、交付物和路径契约
.harness/      工作阶段与本地状态模板
schemas/       配置、报告输入和运行清单 Schema
templates/     可组合 Notebook 章节模板
configs/      项目配置
data/         数据分层目录
sql/          SQL 文件
src/          Python 可复用逻辑
notebooks/    主分析 Notebook
reports/      图表、结果表和最终报告
scripts/      项目生成、验证、复现、审计和报告脚本
tests/        测试与校验
logs/         运行日志
```

## 8. 环境准备

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 9. 配置说明

如需数据库连接：

```text
复制 configs/database.example.yaml 为 configs/database.yaml
填写真实连接信息
确认 configs/database.yaml 不会提交到 Git
```

项目参数位于：

```text
configs/analysis_config.yaml
```

项目结构化契约位于：

```text
project.yaml
```

如在初始化阶段修改了数据源、统计或建模模块，可重新生成 Notebook 骨架：

```bash
python scripts/generate_notebook.py
```

## 10. 运行方式

开发调试时可以打开并局部运行：

```text
notebooks/main_analysis.ipynb
```

正式交付时应从头到尾运行主 Notebook，然后生成报告：

```bash
python scripts/generate_final_report.py
```

可直接执行脚本的功能、输入、输出和注意事项见：

```text
docs/script_catalog.md
```

新增、删除、重命名或修改 `scripts/` 下的脚本时，必须同步更新该文档。

交付前完成自动复现和审计：

```bash
python scripts/validate_project.py
python scripts/run_notebook.py
python scripts/audit_project.py
```

## 11. 输出文件

| 输出文件 | 说明 |
| --- | --- |
| reports/figures/ | 关键图表 |
| reports/tables/ | 结果表 |
| reports/final/ | 最终报告或交付材料 |

报告输入素材：

```text
reports/final/report_inputs.yaml
```

最终报告：

```text
reports/final/final_analysis_report.md
```

报告应基于 `reports/final/final_report_structure.md` 和 `reports/final/report_inputs.yaml` 生成。

## 12. 结果摘要

### 事实

- 待填写

### 推断，如适用

- 待填写

### 建议，如用户明确要求

- 待填写

### 局限性

- 待填写

## 13. 注意事项

- 分析必须基于已确认的业务分析框架。
- 受管修改必须先更新 `docs/change_execution_log.md`，并运行到最远受影响产物。
- 框架、模板、工具或流程缺陷应及时记录到 `docs/framework_issue_log.md`。
- 最终报告结构必须在正式分析前确认。
- 最终报告默认只呈现结果，不自动生成大模型洞察或业务解读。
- 不提交真实数据库凭据。
- 不提交未脱敏敏感数据。
- Notebook 应可从上到下完整复现。
- 关键输出必须保存到 `reports/`。
