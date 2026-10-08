# AEF Docs Init

独立的项目文档初始化、历史资料迁移与落点查询 Skill。当前版本：**0.3.0**。可从默认分支安装，也可使用下文固定版本标签或完整 Release ZIP。

一次建立完整文档分类，以后新增内容也能找到正确位置。不需要先选技术栈，不创建业务应用工程。

- [完整目录树与 73 类落点](references/structure.md)
- [详细使用说明](references/usage.md)
- [已有项目迁移、备份与恢复](references/migration.md)
- [版本变更](CHANGELOG.md)
- [v0.3.0 下载与版本记录](https://github.com/wukongai/aef-docs-init/releases/tag/v0.3.0)

## 解决什么

一次建齐 Product、Project、Engineering、Business、Customer Success、Knowledge 的完整静态目录；已有项目可审阅逐文件映射后迁移历史资料、退役旧导航并修复引用。后续新增内容可查询或检查落点。应用工程初始化和总入口是后续独立能力。

目录树见 [完整结构](references/structure.md)，分类例子与命令参数见 [使用说明](references/usage.md)。动态需求、能力、变更、版本和周期只登记模板，不虚构实例。

## 包结构

```text
aef-docs-init/
├── SKILL.md
├── README.md
├── CHANGELOG.md
├── skill.contract.yaml
├── references/
│   ├── usage.md
│   ├── migration.md
│   └── structure.md
├── templates/
│   ├── directory-contract.json
│   └── migration-policy.json
├── scripts/
│   ├── docs_init.py
│   ├── layout.py
│   ├── safe_files.py
│   ├── docs_migrate.py
│   ├── migration_inventory.py
│   ├── migration_plan.py
│   ├── migration_refs.py
│   └── migration_store.py
└── tests/
    ├── test_docs.py
    ├── test_migration.py
    ├── test_simplification.py
    ├── self-test.json
    └── fixtures/
        ├── directories.json
        ├── routes.json
        └── preserved-routes.json
```

所有依赖都在此目录内；scripts 是 Skill 自身的实现，不会复制成目标项目的工程 scripts 目录。

## 快速安装：普通使用者

需要 Python 3.9 或更新版本，仅标准库。当前测试环境为 macOS；其他平台尚未实测，不宣称已验证兼容。

使用安装器还需要 Node.js/npm。在你希望使用 Skill 的项目终端运行：

```bash
npx skills add wukongai/aef-docs-init
```

`npx` 运行 Skills 安装器；`skills add` 从指定仓库安装；`wukongai/aef-docs-init` 是本仓库。按交互提示选择 `aef-docs-init`、你的 Agent，以及项目级或用户级范围。初次使用建议项目级；不要不加区分地安装到所有宿主。

只想先查看仓库中可用 Skill：

```bash
npx skills add wukongai/aef-docs-init --list
```

`--list` 只列出可用 Skill，不安装。安装器本身可能由 npx 下载。

需要固定使用当前版本：

```bash
npx skills add https://github.com/wukongai/aef-docs-init/tree/v0.3.0
```

这个地址固定到 v0.3.0 标签。安装器用法依据 [Skills 官方说明](https://github.com/vercel-labs/skills)。

安装完成后按宿主要求重新加载 Skill 或开启新会话，请 Agent 确认它能读取 `aef-docs-init/SKILL.md`。不同宿主的自动发现行为需要在你的环境中核验。

## 不用安装器：下载 ZIP

1. 打开 [v0.3.0 Releases](https://github.com/wukongai/aef-docs-init/releases/tag/v0.3.0)，下载 [aef-docs-init-v0.3.0.zip](https://github.com/wukongai/aef-docs-init/releases/download/v0.3.0/aef-docs-init-v0.3.0.zip)。
2. 解压，保留完整 `aef-docs-init/` 文件夹，不要只复制 SKILL.md；脚本、模板和说明都是依赖。
3. 按宿主选择项目 `.agents/skills/aef-docs-init/` 或 `.claude/skills/aef-docs-init/`。希望跨项目使用时，改用该宿主明确的用户级安装位置。
4. 检查最终路径直接包含 `aef-docs-init/SKILL.md`，避免多嵌套一层同名目录。已有同名 Skill 时先保留旧版并审阅差异，不直接覆盖。

GitHub 的 Code → Download ZIP 也能下载源码，但可能对应更新后的默认分支；需要可复现版本时使用 Releases 的版本包。

## 装好以后怎么说

第一次初始化，可以直接对 Agent 说：

> 使用 aef-docs-init，为当前项目初始化完整文档目录。先展示目录和文件预览，保留已有资料，等我确认后再写入。只接入当前使用的 Agent。

如果项目不是当前目录，明确告诉 Agent 目标路径。它会先预览，再等你批准。遇到已有 README 或规则冲突会停止，不会覆盖。

已有项目整理，可以这样说：

> 使用 aef-docs-init，把本项目历史文档迁移到新目录。逐份审阅分类、保留正文和来源，先展示映射、冲突、退役项和备份位置，经我批准后再执行并验证恢复能力。

首次扫描：`python3 -B scripts/docs_migrate.py --target /path/to/project`。它只读清单；具体决策格式、执行批准与恢复命令见 [迁移手册](references/migration.md)。本功能在完整 0.3.0 源码包中可用，固定 v0.1.0 的发行包不包含它。

以后新增文档，可以这样说：

> 使用 aef-docs-init，查询这份数据库选型实验应该放哪里，不要重新初始化。

> 查询搜索功能的拟议规格路径，变更名为 search。

> 检查日报 2026-10-08.md 是否放在正确位置。

普通写作会由项目 Agent 规则引导先查 `docs/README.md`。需要精确分类时才调用只读路由；不是每次写文都重新初始化。

## 不依赖 Agent：直接运行脚本

在解压后的 Skill 包根运行：

```bash
python3 -B scripts/docs_init.py --target /path/to/project --agent codex
```

`-B` 不产生 Python 字节码；`--target` 是实际目标；`--agent codex` 只接入 AGENTS.md。可选 claude、both 或 none；默认 both。路径含空格时用引号括起来。此命令只预览，目标尚不存在时也不会创建。

人工核对并批准后，在同一命令追加 `--apply --approve <预览返回的fingerprint>`。fingerprint 用于检查预览没有漂移，不能替代人的批准。

完成后检查：

```bash
python3 -B scripts/docs_init.py --target /path/to/project --check
```

`--check` 检查目录导航、机器合同和已选入口是否一致，不改文件。

查询文档落点：

```bash
python3 -B scripts/docs_init.py --target /path/to/project --route 拟议规格 --name search
```

`--route` 选择索引中的精确类型，`--name` 提供实例名称。返回 `docs/engineering/changes/search/spec.md`，不写文件。需要核对某个路径时追加 `--validate-path <项目相对路径>`。

## 你会得到什么

- 包含 docs 根在内的 51 个静态目录，每个目录都有 README 用途说明。
- 73 类文档的统一索引，覆盖产品、执行、工程文档、商业、客户成功和知识；类别可共用文件，无需逐类写一份。
- `.aef/docs-layout.json` 独立机器合同；不覆盖现有 `.aef/profile.json`。
- 按选择生成的根 Agent 文档路由规则；选择 none 时不会接入自动读取。

具体需求、版本和变更目录在实际发生时创建。初始化不填充假业务正文，不批准生命周期，也不建立 apps、src、packages 或 deploy 等业务工程目录。

0.3.0 的日常主线是：点子池 → 一份用户故事 → 看板任务流转。PRD 按跨故事方案需要撰写，故事卡 JSON 按自动化需要保留；日报周报共用 logs。六领域及技术架构、选型、方案、测试分类保留。旧项目需审阅迁移，不会自动合并或删除旧正文。

## 常见问题

**已有 docs 能用吗？** 可以。初始化仍不覆盖差异；要整理旧结构，使用独立迁移动作。迁移先逐文件审阅、外部备份，批准后搬迁与修复引用。同名正文差异需人工合并，分类含糊先澄清。

**目录会不会空得太多？** 本版本按完整分类一次建齐，每个目录有 README。实际正文按需要写，不生成假任务或假发布。

**为什么写文还可能放错？** Agent 规则是持续提醒，不是强制 hook；脚本可以校验给定类型与路径，但不会理解所有正文语义。含糊的“调研”“总结”应先确认职责。

**没有 Python 或不想用终端？** Agent 执行脚本同样需要 Python。先准备 Python 3.9+，再让 Agent 操作；不要让它假称脚本已运行。

## 开发与验证

源码学习或二次开发才需要 clone/fork。普通使用者按前面的安装步骤即可。

运行 `python3 -B -m unittest discover -s tests -v`，包括首版 13 项回归和新增迁移测试，验证全目录、路由、冲突、幂等、引用、备份、故障恢复和安全边界。所有写入仅在临时 fixture；测试通过不等于所有宿主或真实项目效果均已验证。

## 发布范围与限制

分发包只包含本目录所列文件；不要打包 owner 仓库、状态记录、内部评审、用户绝对路径或真实项目。本版本未附加 LICENSE 文件。

默认不联网、不装依赖、不写入。迁移需用户批准具体范围，允许修复 profile 和生命周期 manifest 中的路径引用，不改变状态和审批结论。旧 adapter/harness 的兼容性另行评估。通用归档框架不是业务内容模板，不会替用户写出产品定位或宪法。

自动化测试只证明确定性行为；真实项目试用、宿主发现与实际文档归档效果需要单独验证。无全局升级和自动发布动作。
