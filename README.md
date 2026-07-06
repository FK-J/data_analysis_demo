# 数据分析项目模板

这是一个可复用的数据分析项目模板，用于创建可复现、可审计、可交付的数据分析项目。

## 核心约定

- `notebooks/main_analysis.ipynb` 是唯一主分析入口，也是交互式分析工作台。
- `docs/template_usage.md` 是工作流主文档，沉淀新做分析和中途修改需求两类流程。
- `docs/analysis_framework.md` 是具体项目的业务分析框架，正式分析前必须与用户确认。
- `reports/final/final_report_structure.md` 是具体项目的最终报告结构，正式分析前必须确认。
- `docs/script_catalog.md` 记录可直接执行脚本的功能、输入、输出和使用规范。
- `scripts/generate_final_report.py` 根据 `reports/final/report_inputs.yaml` 生成最终报告。
- `reports/` 保存图表、结果表、报告输入素材和最终交付物。

## 快速开始

新项目建议先阅读：

```text
agent.md
docs/template_usage.md
```

然后按 `docs/template_usage.md` 中的工作流推进：

```text
确认业务分析框架
→ 确认最终报告结构
→ 配置数据源和项目参数
→ 在 notebooks/main_analysis.ipynb 中迭代分析
→ 导出图表、结果表和 report_inputs.yaml
→ 运行 scripts/generate_final_report.py
→ 按 docs/08_reproducibility_audit_checklists.md 审计交付
```

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

详细目录职责、Notebook 规范、SQL/Python 规范、数据质量、分析建模、报告交付和审计清单，请查看 `agent.md` 中的文档职责总览。
