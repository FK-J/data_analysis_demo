# 数据分析项目模板

这是一个 Notebook-first 的数据分析项目生成模板，用于快速创建可复现、可审计、可交付的数据分析项目。

## 核心约定

- `notebooks/main_analysis.ipynb` 是唯一主分析入口，也是支持局部迭代的交互式分析工作台。
- `project.yaml` 是项目类型、可选能力、交付物和运行路径的结构化契约。
- `templates/notebook_sections.yaml` 根据项目配置组合主 Notebook 章节。
- `docs/template_usage.md` 是工作流主文档，沉淀新做分析和中途修改需求两类流程。
- `docs/09_change_management_standard.md` 是后续修改的唯一变更管理规范。
- `docs/change_execution_log.md` 记录每次后续修改的执行范围和完成情况。
- `docs/analysis_framework.md` 是具体项目的业务分析框架，正式分析前必须与用户确认。
- `reports/final/final_report_structure.md` 是具体项目的最终报告结构，正式分析前必须确认。
- `docs/framework_issue_log.md` 只记录框架、模板、工具或流程缺陷及改进建议。
- `docs/script_catalog.md` 记录可直接执行脚本的功能、输入、输出和使用规范。
- `scripts/generate_final_report.py` 固定生成最终报告，默认只呈现结果。
- `reports/` 保存图表、结果表、报告输入素材和最终交付物。
- `configs/` 管理项目参数和数据源配置。
- `sql/` 保存可复用 SQL。
- `src/` 保存可复用 Python 逻辑。
- `tests/` 保存关键函数、指标逻辑和数据校验测试。
- `logs/` 保存运行日志和审计信息。
- `scripts/validate_project.py`、`scripts/run_notebook.py` 和 `scripts/audit_project.py` 只负责自动验收，不构成第二套分析入口。

## 快速开始

使用初始化脚本创建具体项目：

```bash
python scripts/init_project.py --output ../customer_retention_analysis --name customer_retention_analysis --display-name "用户留存分析" --analysis-type statistical_analysis --data-source local_file
```

生成器会创建具体分析框架、报告结构，并按项目类型生成 `notebooks/main_analysis.ipynb`。随后按以下顺序处理：

1. 阅读 `agent.md` 和 `docs/` 下的项目规范。
2. 与用户确认业务背景、决策目标、核心业务问题、业务拆解和分析边界。
3. 完成 `docs/analysis_framework.md` 和 `reports/final/final_report_structure.md`，清理所有占位内容。
4. 按需配置私有数据库连接和 `configs/analysis_config.yaml`。
5. 在主 Notebook 中交互完成数据加载、质量检查、分析、验证和结果展示。
6. 将复杂 SQL 放入 `sql/`，将稳定、可复用的 Python 逻辑放入 `src/`，再由 Notebook 调用。
7. 将关键结果导出到 `reports/`，并生成 `reports/final/report_inputs.yaml`。
8. 运行报告生成器和自动验收命令。

完整工作流和规范入口见：

```text
agent.md
docs/template_usage.md
```

然后按 `docs/template_usage.md` 中的工作流推进：

```text
确认业务分析框架
→ 确认最终报告结构
→ 在 change_execution_log.md 登记需求、等级和验收标准
→ 持续记录使用问题和框架改进建议
→ 配置数据源和项目参数
→ 在 notebooks/main_analysis.ipynb 中迭代分析
→ 导出图表、结果表和 report_inputs.yaml
→ 完整运行主 Notebook 并生成最终报告
→ 按 docs/08_reproducibility_audit_checklists.md 审计交付
```

后续修改不能以“文件已改”作为完成标准。必须运行到最远受影响产物，详细规则见 `docs/09_change_management_standard.md`。

## 环境准备

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

## 常用命令

初始化阶段根据 `project.yaml` 生成或更新主 Notebook：

```bash
python scripts/generate_notebook.py
```

生成器只维护标准章节骨架。正式分析后覆盖 Notebook 前必须审阅影响，并按变更管理规范登记和验证。

生成最终报告：

```bash
python scripts/generate_final_report.py
```

如需渲染已准备好的洞察内容：

```bash
python scripts/generate_final_report.py --with-insights
```

运行脚本前，先查看：

```text
docs/script_catalog.md
```

## 敏感信息规则

禁止提交：

- `.env`
- `configs/database.yaml`
- 真实数据库账号、密码、host
- token、密钥、私有连接串
- 未脱敏的敏感明细数据
- 大型原始数据文件

如果必须保留示例数据，必须确认数据已经脱敏，且体积适合进入 Git。

## 自动验证与审计

交付前依次运行：

```bash
python scripts/validate_project.py
python scripts/run_notebook.py
python scripts/audit_project.py
```

- `validate_project.py` 检查配置 Schema、必需文件、Notebook 章节、占位内容、只读 SQL 和敏感文件。
- `run_notebook.py` 在干净内核中从头执行主 Notebook，并将执行副本和 `manifest.json` 保存到 `logs/runs/<run_id>/`。
- `audit_project.py` 检查图表、结果表、报告素材、最终报告和最近一次 Notebook 执行证据。

这些命令是 Notebook 外围的质量门禁；数据分析师日常探索、分析和解释仍在主 Notebook 中完成。

详细目录职责、变更管理、Notebook 规范、SQL/Python 规范、数据质量、分析建模、报告交付和审计清单，请查看 `agent.md` 中的文档职责总览。
