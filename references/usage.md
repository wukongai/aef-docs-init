# 使用与分类说明

新项目初始化使用 docs_init.py。已有项目需要合并旧目录、迁出正文和退役旧导航时，使用 [迁移与恢复](migration.md) 中的 docs_migrate.py；不要仅新增一套目录。只问落点时继续用 --route，不执行迁移。

## 初始化

`python3 -B scripts/docs_init.py --target /path/to/project`：Python 执行本包 CLI；`-B` 不写字节码；`--target` 指定已核实真实目标。默认预览，不建目录。

默认 `--agent both`，预览包含 AGENTS.md 与 CLAUDE.md 的文档落点规则；仅使用一个宿主时可选 codex 或 claude。不需要入口时显式 none，并接受未来手动查索引的限制。存在同名文件差异默认阻断整批；需要给已有入口追加规则时走下面的显式采用流程。

用户明确批准后，用原命令加 `--apply --approve <预览fingerprint>`；`--apply` 才开启写入，指纹用于阻止旧预览被套用。Agent 不能自动把指纹当作人类授权。测试 fixture 可由测试脚本自行批准。

同目标加 `--check`：检查所有静态目录 README、机器合同与选择的入口是否存在且一致。它不扫描正文含义，也不会认为出现陌生旧目录就自动删除或迁移。

### 已有工程基线入口的显式采用

先在包根运行 `python3 -B scripts/docs_init.py --target /path/to/project --agent codex --adopt-agent`。`--adopt-agent` 明确允许预览在本次所选旧根入口末尾追加文档规则，保留所有原字节，包括人工文字和 baseline 管理块。预览的 `agent_adoptions` 列出原件 SHA256、结果 SHA256 和追加正文；此时目标与备份均不写入。标记破损、重复或已有路由正文差异需人工审阅，不自动拼接。

用户批准具体预览后，使用同参数追加 `--apply --approve <fingerprint> --backup /path/outside/project/new-entry-backup`。`--backup` 必须为全新目录，不在目标内，也不能是目标的祖先目录；仅在更新旧入口时必需。先保存 `original/`、`expected/` 和 `record.json`，回读核验后重新核对入口，再逐文件原子替换。旧入口任意字节变化、备份损坏、链接或不安全路径均阻断。新增导航仍按原排他新增流程执行，整批不保证原子性；中途失败保留 `written` 与备份位置。

成功结果返回 `backup` 和 `recovery`。撤销入口采用先运行 `python3 -B scripts/docs_init.py --target /path/to/project --recover-agent /path/outside/project/new-entry-backup`。`--recover-agent` 只预览恢复旧根入口；核对后在同命令加 `--apply --approve <恢复fingerprint>` 才写入。恢复核对备份归属、哈希、当前入口及权限；拒绝覆盖采用后的人工增量。不删除此次新增导航或机器合同，也不回滚工程基线、规范源或其他正文。恢复后根入口未必仍有文档路由，因此再次 `--check` 可能阻断，需要重新采用预览。

入口与备份原件都按完整 UTF-8 字节读取，不转换 CRLF；采用、外部备份和恢复保留旧字节。读取文件的硬链接数必须为 1，否则在采用/恢复前拒绝，不覆盖其他硬链接路径。

反向顺序中，已有完整文档 RULE 外的 baseline 与人工文字继续保留，不需要额外采用。文档总导航和工程导航仅允许原生成正文逐字相同、末尾附加唯一完整的 `<!-- aef:baseline:start -->` / `<!-- aef:baseline:end -->` 块。块外差异、重复/缺失/倒序/内联标记仍阻断；块的完整字节参与预览指纹。检查报告 `external_blocks_unverified`，表示仅安全保留，未验证工程基线块的正文、规则源或宿主生效。

## 新内容落点

### 产品与项目的轻量分工

- 产品定义：`product/product-definition.md`，包含定位与原始意图、用户痛点、价值与替代、商业画布、目标指标和假设。精确类型只登记“产品定义”，不保留旧类型别名。
- 故事地图：`product/story-map.md`，组织用户活动、步骤与 Story 引用，以及发布切片候选，不复制故事正文。
- 点子：先记 `docs/product/ideas.md`，不要求填故事模板。形成需求后在原条目链接故事，避免维护两份正文。
- 用户故事：`requirements/<需求名>/story.md` 包含背景、用户与价值、范围、验收标准。需求发现类型也返回此文件；详细访谈和竞品证据仍放 `product/research/`。
- 故事卡 JSON：只在下游机器接口需要时使用，不要求普通用户手工维护双份；初始化不会生成它。
- PRD：组织多个故事的产品方案，可引用故事；不是每条需求必交一份。
- 看板：`project/board.md` 呈现需求池、待办、进行中、待验收、已完成。任务正文留在 `project/tasks/`，流转不搬文件。任务卡或外部看板为状态唯一来源，本地看板仅作视图或入口；本 Skill 不实现看板同步。
- 迭代计划记录本轮目标、承诺故事、依赖与结果，可引用执行任务，不复制任务状态；日报、周报共用 logs，文件名分别为 `2026-10-09-daily.md`、`2026-W41-weekly.md`。
- 技术架构、技术选型、技术方案、Testing、验证和生效规格仍按原工程分类查询。

旧类型 `待办` 不带名称返回看板；带 `--name login` 返回 `docs/project/tasks/login.md`。`看板` 与 `点子` 为固定文件，不接受名称。日报/周报带名称时自动补类型后缀，接受已带 `.md` 或正确后缀的名称，不接受 `.json`。

普通写作先读 docs/README，由项目规则提供持续提醒。只有需要查分类或核验落点时才调用此 Skill 的路由动作。自然语言判别由 Agent 完成，路径映射由脚本完成。

| 内容意图 | 精确类型 | 预期位置 |
|---|---|---|
| 用户需求、市场问题调研 | 产品调研 | docs/product/research/ |
| 数据库选型、性能实验 | 技术选型实验基线 | docs/engineering/research/ |
| 今天执行了什么 | 日报 | docs/project/logs/ |
| 今天理解了什么原理 | 团队学习 | docs/knowledge/team/learning/ |
| 通用部署与回滚步骤 | 操作部署回滚手册 | docs/engineering/maintenance/runbooks/ |
| 某版本具体回滚证据 | 版本回滚 | docs/product/releases/<版本>/rollback.md |
| 新增能力的拟议规格 | 拟议规格 | docs/engineering/changes/<变更名>/spec.md |
| 已验证评审的能力合同 | 生效规格 | docs/engineering/specs/<能力名>/spec.md |
| 用户操作步骤 | 用户指南 | docs/knowledge/users/guides/ |
| 运营推广内容 | 营销素材 | docs/business/marketing/materials/ |

“调研”“总结”“方案”不足以直接确定目录，应问它记录的是哪种事实；不要按关键词武断归档。

`python3 -B scripts/docs_init.py --target /path/to/project --route 日报 --name 2026-10-08` 返回 `docs/project/logs/2026-10-08-daily.md`。普通目录型条目允许传名称生成 .md 路径；不传名称返回目录。动态条目必须提供名称，固定文件条目不接受名称；待办与日志按上述专用规则解析。

追加 `--validate-path docs/project/logs/2026-10-08-daily.md` 检查是否与类型匹配；失败不写文件。名称允许文字、数字、下划线、中划线和单点版本号；禁止分隔符、父目录穿越和多层路径。完整类型从 docs/README 或机器合同读取。

## 配置与变更

与 aef-product 协作时，五类产物为产品定义、用户与市场研究、Epic/用户故事、故事地图、迭代计划；分别查询精确类型 `产品定义`、`产品调研`、`用户故事`、`故事地图`、`迭代`。初始化只准备目录和索引，正文由产品讨论逐步形成。五类不是固定五个文件，PRD 保持可选。

当前合同将产品定义统一为 product-definition.md，移除旧类型别名。0.3.0 项目仍会触发合同漂移保护：先提供升级预览，审阅现有导航和正文后走迁移流程，不直接重跑 apply 覆盖。已有 positioning.md 先读职责，展示合并候选与 diff；职责不同或含糊时保留原文并请用户决定，不能擅自创建并行类型。CLI 路径检查不判断正文语义。

初始化的独立配置 `.aef/docs-layout.json` 是目录合同投影，不改既有完整 profile。合同与包版本不一致时停止；不能静默迁移。迁移动作可在预览批准后修复 profile/manifest 的路径引用，保留状态和审批事实。未来总入口与工程初始化尚未实现。

各目录 README 是受管理导航；业务正文放索引指定文件。除上面的两个导航附加块外，人工编辑导航后重跑会报冲突，需要审阅整合；不会自动覆盖人工内容。

## 故障恢复

本节说明初始化新增文件的失败边界。入口采用恢复见本页“显式采用”；迁移事务的外部备份、核验与恢复命令见 [迁移手册](migration.md)，两种备份合同不能混用。

全量预检发生在写前，已知冲突不写入。磁盘或权限中途失败仍可能产生部分新增文件和目录；written 列出已开始写入的文件。不要自动删除，检查现场并排除故障后重新预览。要求目标无并发写入，不保证抵御恶意并发链接替换。
