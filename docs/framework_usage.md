# 标准数据分析流程框架使用说明

## 1. 定位与边界

本仓库提供可复制、可个性化调整的标准数据分析流程。维护者负责原始框架；使用者副本独立发展，不需要升级同步、发布服务或复杂插件系统。本轮不新增方法选择索引。

| 内容 | 位置 | 使用方式 |
| --- | --- | --- |
| 框架规范和工具 | `agent.md`、编号规范、`src/project_harness/`、`scripts/`、`schemas/`、默认模板、`.harness/workflow.yaml` | 分析任务期间保持稳定；确需个性化调整时，先调整和验证自己的框架副本，再开展依赖它的任务 |
| 项目配置与契约 | `project.yaml`、`configs/analysis_config.yaml`、`configs/project_contracts.yaml`、分析框架、报告结构 | 按业务填写；这是主要适配入口 |
| 项目实现与产物 | 项目 `src/` 中的业务模块、`sql/`、主 Notebook、数据、报告和日志 | 根据需求开发，Notebook 串联唯一分析流程 |

初始化按 `.harness/template_files.yaml` 白名单复制文件，并重建项目历史、README 和 Notebook；不会自动复制业务新增文件、私有配置、原始数据、历史报告、运行缓存或框架的开发历史。个性化的通用模板文件需要先显式登记到白名单。

初始化入口只接受 template 模式的框架副本，不能把已经填写业务内容的 project 模式项目再次作为通用模板。

## 2. 完整使用步骤

1. 阅读本说明与 `agent.md`；需要个性化调整框架时先完成调整和验证。
2. 执行 `scripts/init_project.py`，设置名称、分析类型和数据源。新项目必须在框架目录之外。
3. 填写业务分析框架与初步报告结构。在 `configs/project_contracts.yaml` 登记关键决策，明确确认依据及最迟解决阶段。非关键未知可以保留，不必一次性确认全部假设。
4. 探索数据，确认实体、粒度、关联、覆盖、缺失和时间语义；登记数据准入结论。数据可对不同用途分别登记为不同 source ID，不能以“文件能读”替代可分析性。
5. 声明少量核心指标和关键对账规则；规则由项目决定，框架不硬编码业务阈值。指标的不同人群、时间或版本使用不同 ID。
6. 用少量素材做报告样张，审阅术语、证据深度和格式。样张不能替代最终数字验收。
7. 在主 Notebook 实施；复杂业务逻辑放在项目模块。需要不同章节时复制默认模板到项目路径，设置 `runtime.notebook_template`；不要覆盖通用模板。生成器和校验器使用同一个配置。
8. 导出检查所需的表和报告素材。`write_report_inputs` 在正式运行内自动绑定运行 ID；日常交互导出不能冒充正式运行产物。
9. 完整运行、生成报告、审计。失败与未验证阻止正式交付；受限数据和不适用章节必须有依据。
10. 审阅最终结果与限制，关闭变更记录，再交付。后续变化按 L0～L3 规范回到最早受影响环节。

正式交付顺序：

```bash
python scripts/validate_project.py --stage spec_confirmed
python scripts/run_notebook.py
python scripts/generate_final_report.py
python scripts/audit_project.py
```

报告渲染放在无界面运行之后，不在正在运行的 Notebook 内调用正式报告 CLI；Notebook 负责计算、检查和导出素材。无需最终报告时设置 `deliverables.final_report: false` 并跳过生成命令。

## 3. 项目契约

使用一个配置文件集中保存以下内容，避免重复维护多份记录：

- `decisions`：ID、确认事项、状态、负责人、依据、最迟解决阶段、未解决影响。`confirmed` 需要非空依据；到期仍 pending/rejected 不得关闭阶段。
- `sources`：ID、输入快照路径、粒度、主键、缺失与时间语义、支持用途、准入结论及证据。`usable/limited` 需可读取的项目内快照；`limited/excluded` 需原因。排除全部来源时必须调整问题。
- `metrics`：核心指标 ID、名称、粒度、人群、分子、分母、时间窗和版本。非比率指标的分母可写“不适用：总量指标”，不能留空。
- `checks`：由项目声明、由框架执行的数据与分析检查。正式验收至少需要各一条 data 和 analysis 检查，空列表显示未验证。
- `report_requirements`：固定 ID、章节或证据主题标题、是否必需。启用最终报告时必须声明。

数据库项目应先在交互探索中保存本轮输入快照，再进行正式运行。SQL 和参数会被记录内容指纹，但只有查询文本不能固定会变化的数据库结果。本轮先支持项目内文件快照追溯，不声称能自动冻结外部数据库或任意环境变量。

可执行检查示例：

```yaml
checks:
  - id: C1
    category: data
    kind: unique
    table: data/processed/customers.csv
    keys: [customer_id]
    description: 客户样本主键唯一且非空
  - id: C2
    category: analysis
    kind: column_relation
    table: reports/tables/retention.csv
    column: lost
    other_column: total
    operator: le
    description: 同人群同时间内流失人数不大于总人数
```

支持 `unique`、`non_null`、`range`、`row_count`、`sum_equals` 和 `column_relation`。范围与行数需要 min/max/expected；跨表求和需要 other_table/other_column；列比较支持 le/eq/ge；数值容差默认 0。数值检查不会忽略缺失或非有限值。它们不是完整业务正确性证明；无法通用表达的逻辑由项目模块验证，并保留测试和人工抽样依据。

## 4. 阶段出口与自动化边界

`workflow.yaml` 是可执行的阶段出口声明。`validate_project.py` 不带 `--stage` 仅做结构预检；带参数时检查该阶段及此前的出口，避免首次运行前就索要未来报告。

| 阶段 | 出口证据 | 用户负责 |
| --- | --- | --- |
| discovery | 配置与结构有效 | 项目选项和范围 |
| spec_confirmed | 框架与报告方案、到期决策已确认 | 问题与确认依据 |
| data_ready | 来源准入结论、输入快照存在 | 数据语义与用途判断 |
| quality_passed | 已声明 data 检查通过 | 检查规则和异常处理 |
| analyzed | 核心口径完整、analysis 检查通过、必要素材导出 | 实现、独立核对依据和解释 |
| validated | 干净内核运行通过，输入与产物指纹匹配 | 启动运行、修复失败 |
| reported | 必需主题覆盖，报告与本次运行绑定 | 样张和最终表达审阅 |
| audited | 前述出口通过，交付物存在且可追溯 | 剩余限制及实际交付判断 |

工程、分析、报告检查分别输出。`unverified` 和 `fail` 都阻止正式验收；`warn` 说明工具覆盖范围外的限制，例如没有 Git。模板模式只验收框架结构，不声称业务阶段通过。

## 5. 报告覆盖和运行追溯

报告输入增加 `coverage`，对每项 requirement 声明 covered、not_applicable 或 missing。covered 至少引用一份本次运行捕获的项目内证据文件；not_applicable 必须说明原因；必需项不能 missing，选填项 missing 也需原因。自然语言的结论是否由证据充分支持，仍由使用者审阅。

汇总与业务问题中的 `metrics` 用注册 ID 标识口径，`value` 保存原始数值，`source` 指定结果表路径、列和行（默认第 0 行）。框架比较两者，容差默认 0；需要浮点容差时由项目显式设置。`format: percent` 只控制呈现，不改变计算值。

```yaml
metrics:
  - id: loss_rate
    name: 流失率
    value: 0.25
    format: percent
    source:
      path: reports/tables/retention.csv
      column: rate
      row: 0
      tolerance: 0.000000000001
    note: 本年度账号粒度
```

```yaml
coverage:
  - id: Q1
    status: covered
    evidence: [reports/tables/retention.csv]
  - id: Q2
    status: not_applicable
    reason: 没有可靠的渠道归属数据，本轮不进行渠道比较
```

每次正式运行保存配置、契约、输入快照、Notebook、代码、SQL、Schema 和工作流的 SHA-256；同时保存执行副本及声明产物的指纹。报告生成前确认这些内容没有变化，生成后记录报告指纹并写入运行 ID。修改输入、代码、素材或报告后，旧验收不能证明新版本有效。

当前正式输出目录仍共享，运行必须串行；本轮不引入并行、增量缓存和升级同步。内容指纹识别版本，不证明文件内容本身的业务正确性。
