# 数据分析项目模板

本项目是一个可复用的数据分析项目骨架，遵循 `agent.md` 和 `docs/` 下的项目规范。

## 1. 项目入口

主分析入口固定为：

```text
notebooks/main_analysis.ipynb
```

所有 SQL 执行、数据加载、清洗、分析、建模、验证和结果导出，都必须能通过该 Notebook 从上到下完整复现。

## 2. 数据库配置

本模板默认使用 MySQL。

创建真实数据库配置时，请复制示例文件：

```text
configs/database.example.yaml
```

为：

```text
configs/database.yaml
```

然后在 `configs/database.yaml` 中填写当前项目实际连接信息。

`configs/database.yaml` 已被 `.gitignore` 忽略，禁止提交真实数据库账号、密码、host 或其他敏感配置。

## 3. 运行方式

1. 安装依赖。
2. 配置 `configs/database.yaml`。
3. 在 Jupyter 中打开 `notebooks/main_analysis.ipynb`。
4. 从上到下顺序执行全部 cell。
5. 检查 `reports/` 下的图表、结果表和最终报告材料。

## 4. 目录说明

详细目录职责见：

```text
docs/02_project_structure.md
```

数据库连接和 SQL 执行规范见：

```text
docs/04_python_sql_database_standard.md
```
