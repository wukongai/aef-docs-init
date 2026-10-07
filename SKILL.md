---
name: aef-docs-init
description: 当用户要求独立初始化完整项目文档目录、确定新增文档落点或检查文档路径一致性时使用。不用于应用工程脚手架、一般正文写作、旧资料自动迁移、生命周期批准或公开发布。
---

# AEF 文档初始化与落点索引

一次建齐完整静态文档目录，让未来内容按同一合同归档。只依赖本包与 Python 标准库，不要求先安装 AEF 工程系统。

## 输入、输出与动作选择

- 输入：用户明确的目标目录；初始化需 Agent 入口范围，默认 `both`，可选 `codex`、`claude`、`none`；路由需精确文档类型和按需实例名称。
- 初始化输出：所有静态文档目录及用途 README、完整索引 `.aef/docs-layout.json`、选择的根 `AGENTS.md` / `CLAUDE.md` 文档规则。
- 路由输出：精确路径，或者必须补充的名称/类型；不写文件、不执行初始化。
- 检查输出：受管理导航、机器合同、Agent 入口的缺失或冲突；给定类型和路径的匹配结果。
- 工程目录、正文生成、版本发布、全局安装不是本 Skill 的动作。

## 工作流

1. 先读 [使用与分类说明](references/usage.md)，完整目录见 [结构说明](references/structure.md)；机器事实源为 [目录合同](templates/directory-contract.json)。确认用户要初始化、查落点还是检查，不让查询动作走初始化。
2. 初始化：在本包根运行 `python3 -B scripts/docs_init.py --target <真实路径>`。默认只读。展示目标、文件清单、入口范围与冲突；目标不是用户明确指定时停止。
3. 用户批准具体预览后，原参数加 `--apply --approve <fingerprint>`；写前全量预检。同一预览指纹只防漂移，不代表用户同意，禁止对真实项目自动复制指纹当授权。
4. 新内容落点：先判断文档职责，有歧义只问关键区别；再执行 `--route <精确类型>`。需要需求名、版本、能力、变更、周期时加 `--name <名称>`。路径校验再加 `--validate-path <项目相对路径>`。查询不会创建实例目录。
5. 初始化后运行同目标的 `--check`；自动从已存配置恢复入口范围。写文任务按返回路径自行执行其写作流程，不重新初始化。新增内容后可以用路径校验确认落点。
6. 汇报实际写入、检查结果、冲突和接入状态。`none` 必须说明未接入 Agent 自动读取，用户需手动查索引。

## 未来写文如何生效

正常写作任务不必每次触发此 Skill：根 Agent 规则要求先查 docs/README；需要明确分类或检查路径时触发本 Skill 的只读动作。自然语言规则不是硬门禁，不能保证 Agent 永不放错；脚本校验给定类型与路径，不替用户判断正文语义。

已有入口包含完全相同的规则段时保留原文；其他差异整批阻断，用户审阅后另行合并。不静默追加，不靠旁路文件冒充已经接入。

## 停止与失败

- 已有 README、机器合同、入口有差异：停止并展示路径；不覆盖、不搬迁旧文件。若用户明确选择 none，只生成文档与独立配置，并报告接入缺口。
- 目标或内部路径有链接、穿越、非常规文件：拒绝。实例名禁止路径分隔符和父目录片段；不要把参考项目当目标。
- 执行期间要求无并发写入。采用排他新增，不是跨文件原子事务；失败可能留下新增文件/目录，输出 written 清单，保留现场后重新预览，不自动删除。
- 路由缺类型、实例名称或类别含糊：停止询问，不猜位置。合同漂移需评审迁移，不能用旧规则继续新增。
- 不生成虚构业务文档，不批准宪法或阶段；凭证、真实客户明细和运行日志不进入文档仓。

## 示例与验证

“初始化文档目录” → 完整预览 → 批准 → apply → check。

“技术选型实验放哪里” → `--route 技术选型实验基线` → engineering/research，不执行初始化。

“新增搜索能力的拟议规格” → `--route 拟议规格 --name search` → docs/engineering/changes/search/spec.md；生效规格是另一类型，评审通过后才更新。

运行 `python3 -B tests/test_docs.py` 进行临时 fixture 验证。声明式入口为 [tests/self-test.json](tests/self-test.json)，分类与目录 fixture 位于 [tests/fixtures/routes.json](tests/fixtures/routes.json) 和 [tests/fixtures/directories.json](tests/fixtures/directories.json)。

发布、安装与支持边界见 [README](README.md)，完整执行边界见 [skill.contract.yaml](skill.contract.yaml)。
