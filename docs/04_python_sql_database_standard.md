# 04. Python、SQL 与数据库规范

## 1. Python 脚本定位

Python 脚本用于沉淀可复用逻辑。它们不是最终分析入口，必须由 `notebooks/main_analysis.ipynb` 调用。

适合放入 Python 脚本的内容：

- 数据库连接。
- SQL 文件读取和执行。
- 数据加载与保存。
- 数据质量检查。
- 数据清洗函数。
- 指标计算函数。
- 特征工程函数。
- 统计检验函数。
- 模型训练与评估函数。
- 通用可视化函数。
- 报告素材导出函数。

不应该放入 Python 脚本的内容：

- 当前项目的核心分析叙事。
- 只执行一次且需要解释的业务判断。
- 最终结论。

## 2. Python 脚本设计要求

Python 脚本必须遵守：

- 函数命名清晰，表达业务含义或处理目的。
- 输入和输出明确。
- 不依赖 Notebook 中的全局变量。
- 不在函数内部静默读取不相关文件。
- 不在函数内部静默修改原始数据。
- 关键函数应该有 docstring。
- 复杂函数应该有必要的单元测试或样例调用。

禁止在 Python 脚本中硬编码：

- 数据库账号和密码。
- 生产库 host。
- 用户本地绝对路径。
- 私钥、token、cookie。
- 与项目口径相关但未记录的魔法数字。

## 3. 推荐 Python 模块结构

```text
src/
  db/
    connection.py
    sql_runner.py
  io/
  quality/
  cleaning/
  features/
  analysis/
  stats/
  modeling/
  visualization/
  reporting/
```

模块职责：

- `src/db/`：数据库连接和 SQL 执行。
- `src/io/`：本地文件读写、缓存、导出。
- `src/quality/`：数据质量检查。
- `src/cleaning/`：清洗规则。
- `src/features/`：特征工程。
- `src/analysis/`：业务指标和分析函数。
- `src/stats/`：统计检验和回归分析。
- `src/modeling/`：模型训练、评估和解释。
- `src/visualization/`：通用绘图函数。
- `src/reporting/`：报告素材导出。

## 4. 数据库连接方式

后续项目可以通过 Python 直接连接数据库并执行 SQL 脚本。

数据库连接信息必须来自以下来源之一：

- `.env` 文件。
- 环境变量。
- 未提交到版本库的本地配置文件。
- 受权限保护的密钥管理服务。

项目只能提交 `.env.example` 或 `configs/database.example.yaml`，禁止提交真实 `.env` 和真实数据库凭据。

## 5. 推荐数据库模块

数据库相关逻辑应该放在：

```text
src/db/connection.py
src/db/sql_runner.py
```

`connection.py` 应该负责：

- 读取数据库连接配置。
- 创建数据库连接或 SQLAlchemy engine。
- 设置只读连接优先。
- 处理连接关闭和异常。

`sql_runner.py` 应该负责：

- 读取指定 SQL 文件。
- 支持传入安全参数。
- 执行 SQL。
- 返回 pandas DataFrame 或执行状态。
- 记录 SQL 文件路径、运行时间和返回行数。

## 6. SQL 执行要求

Notebook 中执行 SQL 时必须说明：

- 执行了哪个 SQL 文件。
- SQL 的用途是什么。
- 使用了哪些参数。
- 结果返回多少行、多少列。
- 是否通过数据校验。

SQL 执行默认应为只读查询。涉及写库、删表、更新、建表、覆盖表的 SQL，必须显式说明风险，并在执行前由用户确认。

禁止在 Notebook 或 Python 中拼接未校验的用户输入作为 SQL 字符串。

## 7. SQL 文件头部规范

每个 SQL 文件必须包含头部说明：

```sql
-- purpose: 说明 SQL 的用途
-- input: 说明输入表或视图
-- output: 说明输出结果或目标对象
-- grain: 说明结果粒度，例如一行代表一个用户、一个订单或一天
-- date_range: 说明时间范围来源，例如由 notebook 参数控制
-- filters: 说明核心过滤条件
-- notes: 说明特殊口径、风险或注意事项
```

示例：

```sql
-- purpose: 抽取已支付订单明细数据
-- input: ods.orders, ods.users
-- output: pandas DataFrame: orders_df
-- grain: 一行代表一笔订单
-- date_range: 由 notebook 参数 start_date 和 end_date 控制
-- filters: 仅保留 paid_status = 'paid' 的订单
-- notes: 不包含退款订单，退款分析需使用单独 SQL

select
    order_id,
    user_id,
    paid_at,
    order_amount
from ods.orders
where paid_status = 'paid'
  and paid_at >= :start_date
  and paid_at < :end_date;
```

## 8. SQL 编写规范

SQL 必须清晰、可读、可复查。

必须遵守：

- 使用清晰的字段别名。
- 明确 join 条件。
- 明确时间范围。
- 明确过滤条件。
- 避免 `select *`，除非是在临时探索阶段。
- 避免隐式类型转换。
- 避免无说明地去重。
- 复杂 SQL 应使用 CTE 分层表达。

禁止出现：

- 未说明原因的 `distinct`。
- 未说明原因的删除、覆盖或更新操作。
- 依赖数据库默认排序的结果逻辑。
- 未限定时间范围的大表全量查询。

## 9. Notebook 调用要求

主 Notebook 中必须通过 Python 调用 SQL 文件，而不是只粘贴查询结果。

推荐流程：

```text
读取配置
→ 创建数据库连接
→ 读取 SQL 文件
→ 注入安全参数
→ 执行 SQL
→ 返回 DataFrame
→ 记录行数、列数、执行时间
→ 执行数据校验
```

如果项目无法直连数据库，必须在 Notebook 中说明：

- 数据由谁导出。
- 导出时间。
- 导出 SQL 或口径。
- 文件保存位置。
- 是否存在数据时效性风险。

## 10. 安全要求

禁止：

- 在 Notebook 中写真实数据库密码。
- 在 Python 脚本中写真实数据库密码。
- 在 SQL 文件中写密钥或 token。
- 将真实 `.env` 提交到版本库。
- 在日志中打印连接字符串。
- 将生产库敏感表明细导出到可提交目录。

涉及写库、删表、更新、建表、覆盖表的 SQL，必须显式标注风险，默认不执行。
