# 使用与分类说明

## 初始化

`python3 -B scripts/docs_init.py --target /path/to/project`：Python 执行本包 CLI；`-B` 不写字节码；`--target` 指定已核实真实目标。默认预览，不建目录。

默认 `--agent both`，预览包含 AGENTS.md 与 CLAUDE.md 的文档落点规则；仅使用一个宿主时可选 codex 或 claude。不需要入口时显式 none，并接受未来手动查索引的限制。存在同名文件差异会阻断整批，不覆盖、不追加。

用户明确批准后，用原命令加 `--apply --approve <预览fingerprint>`；`--apply` 才开启写入，指纹用于阻止旧预览被套用。Agent 不能自动把指纹当作人类授权。测试 fixture 可由测试脚本自行批准。

同目标加 `--check`：检查所有静态目录 README、机器合同与选择的入口是否存在且一致。它不扫描正文含义，也不会认为出现陌生旧目录就自动删除或迁移。

## 新内容落点

普通写作先读 docs/README，由项目规则提供持续提醒。只有需要查分类或核验落点时才调用此 Skill 的路由动作。自然语言判别由 Agent 完成，路径映射由脚本完成。

| 内容意图 | 精确类型 | 预期位置 |
|---|---|---|
| 用户需求、市场问题调研 | 产品调研 | docs/product/research/ |
| 数据库选型、性能实验 | 技术选型实验基线 | docs/engineering/research/ |
| 今天执行了什么 | 日报 | docs/project/logs/daily/ |
| 今天理解了什么原理 | 团队学习 | docs/knowledge/team/learning/ |
| 通用部署与回滚步骤 | 操作部署回滚手册 | docs/engineering/maintenance/runbooks/ |
| 某版本具体回滚证据 | 版本回滚 | docs/product/releases/<版本>/rollback.md |
| 新增能力的拟议规格 | 拟议规格 | docs/engineering/changes/<变更名>/spec.md |
| 已验证评审的能力合同 | 生效规格 | docs/engineering/specs/<能力名>/spec.md |
| 用户操作步骤 | 用户指南 | docs/knowledge/users/guides/ |
| 运营推广内容 | 营销素材 | docs/business/marketing/materials/ |

“调研”“总结”“方案”不足以直接确定目录，应问它记录的是哪种事实；不要按关键词武断归档。

`python3 -B scripts/docs_init.py --target /path/to/project --route 日报 --name 2026-10-08` 返回 `docs/project/logs/daily/2026-10-08.md`。目录型条目允许传名称生成 .md 路径；不传名称返回目录。动态条目必须提供名称，固定文件条目不接受名称。

追加 `--validate-path docs/project/logs/daily/2026-10-08.md` 检查是否与类型匹配；失败不写文件。名称允许文字、数字、下划线、中划线和单点版本号；禁止分隔符、父目录穿越和多层路径。完整类型从 docs/README 或机器合同读取。

## 配置与变更

独立配置 `.aef/docs-layout.json` 是已安装的目录合同投影，不改既有完整 profile。合同与包版本不一致时停止；不能静默迁移。未来总入口与工程初始化可读取这一合同，但本版本没有实现它们。

各目录 README 是受管理导航；业务正文放索引指定文件。人工编辑导航后重跑会报冲突，需要审阅整合；不会自动覆盖人工内容。

## 故障恢复

全量预检发生在写前，已知冲突不写入。磁盘或权限中途失败仍可能产生部分新增文件和目录；written 列出已开始写入的文件。不要自动删除，检查现场并排除故障后重新预览。要求目标无并发写入，不保证抵御恶意并发链接替换。
