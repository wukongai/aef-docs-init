# AEF 文档初始化助手（AEF Docs Init / aef-docs-init）：安装与使用手册

这份手册帮助你使用 **aef-docs-init**：一次建好项目文档目录，以后新增内容也知道放在哪里，并介绍已有项目的历史资料迁移流程。

**当前 GitHub main 源码版本为 0.3.2。下方一条命令安装的是当前源码；历史 v0.3.0 Release 不包含本轮产品定义与故事地图类型，请勿与当前源码混淆。**

它是独立 Skill，不要求先安装整套 AEF，也不要求先选前端、后端或数据库。它只处理文档，不创建应用工程。

## 1. 先知道它能做什么

| 动作 | 你得到的结果 |
|---|---|
| 初始化文档体系 | 51 个静态目录（含 docs 根），每个目录都有用途说明 |
| 查询新增内容落点 | 从 74 类文档映射中返回具体目录或文件路径 |
| 检查目录与路径 | 检查索引、配置、Agent 入口，以及给定文档的路径 |
| 历史文档迁移 | 审阅逐文件分类后，备份并迁移旧资料、修复引用 |
| 迁移核验与恢复 | 核对来源和目标哈希，必要时预览并批准恢复 |

六大分类分别是：

- **产品**：定位、路线图、需求、用户故事、版本发布。
- **项目执行**：任务、Sprint、风险、会议、日报、交接。
- **工程文档**：架构、技术调研、规格、变更包、接口、运维知识。
- **商业**：定价、营销、销售、指标。
- **客户成功**：内测、接入、反馈、支持、复盘。
- **知识**：团队学习与教程、用户指南、参考资料。

所有静态分类一次建好。某个需求、版本或变更对应的实例目录，等真实内容出现时再建，不会创建假的版本或任务。

## 2. 下载和安装

GitHub 仓库：[AEF Docs Init](https://github.com/wukongai/aef-docs-init)。

备用下载：[当前完整源码 ZIP](https://github.com/wukongai/aef-docs-init/archive/refs/heads/main.zip)。

### 方式一：安装器，适合大多数用户

电脑需要 Node.js/npm、Git，以及执行 Skill 脚本所需的 Python 3.9+。私有仓库需要已有访问权限与本机 Git 认证。

打开终端，为本机 Codex 安装，复制这一条命令：

```bash
npx skills add wukongai/aef-docs-init --skill aef-docs-init --agent codex --global
```

这条命令自动下载并安装完整 Skill，不需要手动解压或找文件夹。`--skill` 选择文档初始化 Skill，`--agent codex` 指定 Codex，`--global` 表示本机多个项目可用。按提示确认即可；已有同名安装或个人修改时先保留旧版，不直接覆盖。

Claude Code 用户把 `--agent codex` 换成 `--agent claude-code`。只用于当前项目时，进入该项目终端并去掉 `--global`。安装器显示实际位置；`~` 代表你自己的用户主目录，不是作者的电脑路径。

只想先看有没有这个 Skill，可以运行：

```bash
npx skills add wukongai/aef-docs-init --list
```

`--list` 只查看，不安装 Skill；npx 可能先下载安装器本身。

### 方式二：手动下载 ZIP

到上面的当前完整源码 ZIP 链接下载，解压后保留整个 `aef-docs-init` 文件夹。不要只复制 SKILL.md，内部脚本与模板也要一起保留。

按你的 Agent 选择项目入口：

- 通用 Agent/Codex 项目入口：`.agents/skills/aef-docs-init/`。
- Claude Code 项目入口：`.claude/skills/aef-docs-init/`。

最终应能直接看到 `aef-docs-init/SKILL.md`。避免多嵌套一层同名目录。已有同名 Skill 时保留旧版，先比较，不直接覆盖。

安装后按宿主要求刷新 Skill 或开启新会话，请 Agent 确认能读取这个 Skill。具体自动发现行为以你的宿主环境为准。

## 3. 第一次初始化：直接复制这段话

> 使用 aef-docs-init，为当前项目初始化完整文档目录。先展示将创建的目录和文件，保留已有资料，等我确认后再写入。只接入我当前使用的 Agent。

如果你操作的不是当前项目，明确补充项目路径。不要只说“那个项目”，避免 Agent 选错目录。

正常过程应该是：

1. Agent 读取 Skill、完整结构和操作说明。
2. 运行只读预览，列出要新增的目录、配置和入口。
3. 你核对目标与清单，明确确认。
4. Agent 执行写入，再运行检查。
5. Agent 汇报实际结果和未完成事项。

看到已有文件冲突时，应先处理冲突。不要要求它强行覆盖，也不要把“已经生成预览”当成“已经初始化”。

## 4. 初始化后去哪里看

先打开项目的 `docs/README.md`，这是文档总导航。每个子目录也有自己的 README。

`.aef/docs-layout.json` 保存机器可读映射。根目录的 AGENTS.md 或 CLAUDE.md 提醒 Agent 在新增文档前查索引。Skill 默认可生成两种入口；你可以只选当前宿主，或明确选择不接入入口。

选择不接入入口时，目录仍可使用，但以后需要手动提醒 Agent 查索引。

这些 README 是受管理导航；业务正文写到索引对应位置。直接改动导航后再次初始化，工具会报告差异，不会覆盖你的修改。

## 5. 以后新增内容：不必重新初始化

可以直接说：

> 使用 aef-docs-init，查询这份数据库选型实验应该放在哪里，只查询，不初始化。

结果应指向 `docs/engineering/research/`。

> 查询搜索能力的拟议规格应该放哪里，变更名是 search。

结果应为 `docs/engineering/changes/search/spec.md`。

> 今天写的是学习收获，不是执行日报，请帮我查正确目录。

结果应指向 `docs/knowledge/team/learning/`，而不是执行日志。

这一步只返回路径，不创建正文。你可以继续要求负责写作的 Agent 按该位置撰写，写后再检查路径。

## 6. 最容易混淆的几组内容

| 你在记录什么 | 对应位置 |
|---|---|
| 市场、用户问题与产品机会 | product/research |
| 数据库选型、性能测试与技术实验 | engineering/research |
| 今天完成了哪些工作 | project/logs |
| 今天学到了什么 | knowledge/team/learning |
| 通用部署与回滚步骤 | engineering/maintenance/runbooks |
| 某版本具体回滚与验证证据 | product/releases/对应版本 |
| 本次变更拟议采用的规格 | engineering/changes/对应变更 |
| 已通过验证和评审的能力规格 | engineering/specs/对应能力 |

表中路径都位于 `docs/` 下。“调研”“总结”“方案”这些词本身不够明确，要先判断记录的是哪种事实。

## 7. 检查是否真正可用

完成首次初始化后，让 Agent：

> 检查 aef-docs-init 的目录、机器合同和 Agent 入口是否一致；再查询一次“用户指南”的落点，不修改文件。

你应能找到完整目录、清晰的总导航，并得到 `docs/knowledge/users/guides/` 的查询结果。

自动化检查覆盖目录、路由、备份、引用修复及恢复等行为；实际项目仍需核验落点和原资料是否保留。测试不等于真实项目试用或旧工程运行时兼容认证，也不能保证 Agent 永远不会归错类。

## 8. 已有项目的历史文档怎么整理

这项能力适用于项目已经有旧 docs、历史文件夹或自定义分类的情况。请使用当前完整源码包；先审阅迁移方案，避免只添加新目录而留下两套结构并存。

可以直接对 Agent 说：

> 使用 aef-docs-init，整理当前项目历史文档并合并到六领域目录。先读正文和项目规则，展示逐文件旧路径到新路径、分类依据、冲突、旧导航退役项和外部备份位置。分类含糊先问我，经我批准同一预览后再执行；保留正文、需求状态、审批事实和来源，最后核验并说明如何恢复。

正常流程是：

1. **只读扫描**：列出历史文档、入口及配置引用，不修改文件。
2. **逐文件分类**：说明保留、迁移或退役的依据。“调研”“总结”等含糊标题不能直接决定归属。
3. **预览与批准**：审阅具体映射、冲突和移除项。指纹只防止预览后文件变化，不能代替你的授权。
4. **先备份再执行**：原件保存到项目范围外的新目录，回读核验后才搬迁。旧导航、空模板须核验后退役；非空目录不强删。
5. **修复与核验**：修复支持范围内的链接、Agent 文档规则和 JSON 路径字段，保留状态与审批结论，核对来源及最终文件哈希。

同名不同内容不会自动覆盖或拼接，需要先人工审阅合并后重新预览。迁移脚本不替你重写业务正文。

需要直接运行时，在当前完整 Skill 包根执行：

```bash
python3 -B scripts/docs_migrate.py --target /path/to/project
```

`-B` 不产生字节码；`--target` 指定已有项目真实路径。默认只扫描。Agent 依据正文准备项目范围外的 decisions.json 后，加 `--decisions /path/to/decisions.json` 生成迁移预览。决策格式见包内 `references/migration.md`。

批准具体预览后执行：

```bash
python3 -B scripts/docs_migrate.py --target /path/to/project --decisions /path/to/decisions.json --apply --approve FINGERPRINT --backup /path/to/new-external-backup
```

`--apply` 才开始写入；`--approve` 使用已获批准的同一预览指纹；`--backup` 指向尚不存在、位于项目范围外的备份目录。预览与执行的入口选择和额外引用范围必须一致。

完成后，用 `--verify /path/to/new-external-backup` 核验结果，再运行初始化 CLI 的 `--check` 检查目录合同。

**失败后如何恢复？** 先保留现场，用下面的命令查看恢复清单：

```bash
python3 -B scripts/docs_migrate.py --target /path/to/project --recover /path/to/new-external-backup
```

默认只预览。审阅并批准后，再加 `--apply --approve RECOVERY_FINGERPRINT` 执行恢复。若已有人工新改动、备份损坏或不明丢失，工具会停止，不强行覆盖。

迁移和恢复期间应暂停并发写入。自动检查包括普通 Markdown 链接、引用定义和明确 JSON 路径字段；外部网址、动态表达式、HTML、短名 Wiki 链接和二进制内部引用不在自动验证范围。项目范围外的其他配置需明确申报或人工处理。文档迁移完成不表示旧 adapter、harness 或生命周期工具已支持新布局。

## 9. 常见问题

**已有项目可以用吗？** 可以。遇到已有导航或入口差异会停止；通过独立迁移流程，经逐文件审阅、备份和批准后整理旧结构，不会直接覆盖原资料。

**会生成工程代码吗？** 不会。工程初始化和总入口属于后续独立能力。

**会写好所有业务文档吗？** 不会。它建立分类与说明，不编造定位、需求、客户记录或版本成果。

**直接运行需要什么？** Python 3.9+，只用标准库。让 Agent 执行也需要可用的 Python 环境。

**只下载了 SKILL.md 能用吗？** 不完整。请保留整个包的 scripts、templates、references 和 tests。

**需要更新版本吗？** 先阅读对应版本说明并保留现有版本；不要强行覆盖已修改的导航或规则。

完整参数和目录树请查看 GitHub README。安装器命令参照 [Skills 官方说明](https://github.com/vercel-labs/skills)。
