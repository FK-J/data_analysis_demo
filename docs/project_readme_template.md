# 项目名称

简要说明本数据分析项目要解决的问题，以及面向的业务场景。

## 1. 项目背景

- 业务背景：
- 决策场景：
- 核心问题：
- 预期交付物：

## 2. 数据来源

| 数据源 | 说明 | 时间范围 | 粒度 | 负责人 |
| --- | --- | --- | --- | --- |
| 待填写 | 待填写 | 待填写 | 待填写 | 待填写 |

如使用数据库，请说明 profile 名称，不要写真实账号、密码或 host。

## 3. 核心指标口径

| 指标 | 口径 | 粒度 | 备注 |
| --- | --- | --- | --- |
| 待填写 | 待填写 | 待填写 | 待填写 |

## 4. 项目结构

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

## 5. 环境准备

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 6. 配置说明

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

## 7. 运行方式

打开并从上到下运行：

```text
notebooks/main_analysis.ipynb
```

## 8. 输出文件

| 输出文件 | 说明 |
| --- | --- |
| reports/figures/ | 关键图表 |
| reports/tables/ | 结果表 |
| reports/final/ | 最终报告或交付材料 |

## 9. 结论摘要

### 事实

- 待填写

### 推断

- 待填写

### 建议

- 待填写

### 局限性

- 待填写

## 10. 注意事项

- 不提交真实数据库凭据。
- 不提交未脱敏敏感数据。
- Notebook 应可从上到下完整复现。
- 关键输出必须保存到 `reports/`。
