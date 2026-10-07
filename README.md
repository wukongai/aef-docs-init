# AEF Docs Init

独立的项目文档目录初始化与落点查询 Skill。版本：**0.1.0**。

一次建立完整文档分类，以后新增内容也能找到正确位置。不需要先选技术栈，不创建业务应用工程。

- [完整目录树与 71 类落点](references/structure.md)
- [详细使用说明](references/usage.md)
- [v0.1.0 下载与版本记录](https://github.com/wukongai/aef-docs-init/releases/tag/v0.1.0)

## 解决什么

一次建齐 Product、Project、Engineering、Business、Customer Success、Knowledge 的完整静态目录；每个目录有用途说明和路径索引。后续新增内容可查询或检查其落点。应用工程初始化和总入口是后续独立能力。

目录树见 [完整结构](references/structure.md)，分类例子与命令参数见 [使用说明](references/usage.md)。动态需求、能力、变更、版本和周期只登记模板，不虚构实例。

## 包结构

```text
aef-docs-init/
├── SKILL.md
├── README.md
├── skill.contract.yaml
├── references/
│   ├── usage.md
│   └── structure.md
├── templates/directory-contract.json
├── scripts/
│   ├── docs_init.py
│   ├── layout.py
│   └── safe_files.py
└── tests/
    ├── test_docs.py
    ├── self-test.json
    └── fixtures/
        ├── directories.json
        └── routes.json
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

需要固定使用首版：

```bash
npx skills add https://github.com/wukongai/aef-docs-init/tree/v0.1.0
```

这个地址固定到 v0.1.0 标签。安装器用法依据 [Skills 官方说明](https://github.com/vercel-labs/skills)。

安装完成后按宿主要求重新加载 Skill 或开启新会话，请 Agent 确认它能读取 `aef-docs-init/SKILL.md`。不同宿主的自动发现行为需要在你的环境中核验。

## 不用安装器：下载 ZIP

1. 打开 [v0.1.0 Releases](https://github.com/wukongai/aef-docs-init/releases/tag/v0.1.0)，下载 `aef-docs-init-v0.1.0.zip`。
2. 解压，保留完整 `aef-docs-init/` 文件夹，不要只复制 SKILL.md；脚本、模板和说明都是依赖。
3. 按宿主选择项目 `.agents/skills/aef-docs-init/` 或 `.claude/skills/aef-docs-init/`。希望跨项目使用时，改用该宿主明确的用户级安装位置。
4. 检查最终路径直接包含 `aef-docs-init/SKILL.md`，避免多嵌套一层同名目录。已有同名 Skill 时先保留旧版并审阅差异，不直接覆盖。

GitHub 的 Code → Download ZIP 也能下载源码，但可能对应更新后的默认分支；需要可复现版本时使用 Releases 的版本包。

## 装好以后怎么说

第一次初始化，可以直接对 Agent 说：

> 使用 aef-docs-init，为当前项目初始化完整文档目录。先展示目录和文件预览，保留已有资料，等我确认后再写入。只接入当前使用的 Agent。

如果项目不是当前目录，明确告诉 Agent 目标路径。它会先预览，再等你批准。遇到已有 README 或规则冲突会停止，不会覆盖。

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

- 包含 docs 根在内的 54 个静态目录，每个目录都有 README 用途说明。
- 71 类文档的统一索引，覆盖产品、执行、工程文档、商业、客户成功和知识。
- `.aef/docs-layout.json` 独立机器合同；不覆盖现有 `.aef/profile.json`。
- 按选择生成的根 Agent 文档路由规则；选择 none 时不会接入自动读取。

具体需求、版本和变更目录在实际发生时创建。初始化不填充假业务正文，不批准生命周期，也不建立 apps、src、packages 或 deploy 等业务工程目录。

## 常见问题

**已有 docs 能用吗？** 可以预览。已有同名导航或入口不一致会整批停止，需要先审阅整合；业务文档不移动、不删除。

**目录会不会空得太多？** 本版本按完整分类一次建齐，每个目录有 README。实际正文按需要写，不生成假任务或假发布。

**为什么写文还可能放错？** Agent 规则是持续提醒，不是强制 hook；脚本可以校验给定类型与路径，但不会理解所有正文语义。含糊的“调研”“总结”应先确认职责。

**没有 Python 或不想用终端？** Agent 执行脚本同样需要 Python。先准备 Python 3.9+，再让 Agent 操作；不要让它假称脚本已运行。

## 开发与验证

源码学习或二次开发才需要 clone/fork。普通使用者按前面的安装步骤即可。

运行 `python3 -B tests/test_docs.py`，13 项测试在临时目录验证全目录、路由、冲突、幂等和安全边界。测试不会初始化真实项目。测试通过不等于所有宿主或业务场景均已验证。

## 发布范围与限制

分发包只包含本目录所列文件；不要打包 owner 仓库、状态记录、内部评审、用户绝对路径或真实项目。本版本未附加 LICENSE 文件。

默认不联网、不装依赖、不迁移旧资料，不修改 .aef/profile.json 或生命周期 manifest。遇到已有导航/规则冲突会停止，可能需要人工整合后重新预览。通用归档框架不是业务内容模板，不会替用户写出产品定位或宪法。

自动化测试只证明确定性行为；真实项目试用、宿主发现与实际文档归档效果需要单独验证。无全局升级和自动发布动作。
