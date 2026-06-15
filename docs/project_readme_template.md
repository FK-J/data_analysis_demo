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

如用户提出新的分析需求，应先更新 `docs/analysis_framework.md`，再同步 Notebook、SQL、Python 和报告。

## 3. 数据来源

| 数据源 | 说明 | 时间范围 | 粒度 | 负责人 |
| --- | --- | --- | --- | --- |
| 待填写 | 待填写 | 待填写 | 待填写 | 待填写 |

如使用数据库，请说明 profile 名称，不要写真实账号、密码或 host。

## 4. 核心指标口径

| 指标 | 口径 | 粒度 | 备注 |
| --- | --- | --- | --- |
| 待填写 | 待填写 | 待填写 | 待填写 |

## 5. 项目结构

```text
configs/      项目配置
data/         数据分层目录
sql/          SQL 文件
src/          Python 可复用逻辑
notebooks/    主分析 Notebook
reports/      图表、结果表和最终报告
tests/        测试与校验
logs/         运行日志
```

## 6. 环境准备

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 7. 配置说明

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

## 8. 运行方式

打开并从上到下运行：

```text
notebooks/main_analysis.ipynb
```

## 9. 输出文件

| 输出文件 | 说明 |
| --- | --- |
| reports/figures/ | 关键图表 |
| reports/tables/ | 结果表 |
| reports/final/ | 最终报告或交付材料 |

最终完整数据分析报告建议保存为：

```text
reports/final/final_analysis_report.md
```

报告应围绕 `docs/analysis_framework.md` 中确认的业务问题组织。

## 10. 结论摘要

### 事实

- 待填写

### 推断

- 待填写

### 建议

- 待填写

### 局限性

- 待填写

## 11. 注意事项

- 分析必须基于已确认的业务分析框架。
- 不提交真实数据库凭据。
- 不提交未脱敏敏感数据。
- Notebook 应可从上到下完整复现。
- 关键输出必须保存到 `reports/`。
