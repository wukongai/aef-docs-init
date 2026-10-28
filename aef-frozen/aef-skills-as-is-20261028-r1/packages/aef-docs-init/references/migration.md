# 已有项目历史文档迁移与恢复

迁移处理已有资料、旧目录和引用关系。新项目仍用 docs_init.py；查路径仍用其 --route。0.3.0 源码包含本能力，固定 v0.1.0 的发行包不包含本能力。

## 0.3.0 分类升级

旧版机器合同会触发漂移阻断，不能直接重跑初始化覆盖。先逐文件审阅：discovery.md 与 user-story.md 拟归同一 story.md 时，内容不同会阻断，不会自动摘要丢内容；先保留原件并审阅合并结果，再单独预览迁移。story-card.json 保留为可选机器接口，不自动转换。backlog 正文归 tasks，看板只引用任务；日报周报分别映射为 logs/<日期>-daily.md、logs/<周期>-weekly.md。旧导航逐项核验后才能退役。扫描只判断目录域，不能自动发现所有旧版细分类，请显式审阅这些路径。真实项目迁移仍需单独批准文件映射与备份。

## 对 Agent 怎么说

> 用 aef-docs-init 整理当前项目的历史文档，合并到六领域目录。先读正文和项目规则，展示逐文件旧→新映射、依据、同名冲突、旧导航退役清单和备份位置。分类含糊先问我，批准本次预览后再执行；保留需求状态、历史结论和来源，完成后验证引用与可恢复性。

Agent 先读项目约束与目录合同，再盘点已有内容。不得把目录名或文件标题当成充分分类依据；例如“调研”可能是产品用户调研，也可能是技术实验。已有明确批准只适用于同一未漂移范围，不能扩展到新增资料或另一项目。

## 1. 扫描

在 Skill 包根运行：

```bash
python3 -B scripts/docs_migrate.py --target /path/to/project
```

`-B` 避免字节码，`--target` 指定已经存在的真实项目。输出文件清单、哈希、目录与需审阅项；不建文件、不搬迁。扫描 docs 全树、.aef 下 JSON、根 README/AGENTS/CLAUDE 以及 .claude/rules、.agents/rules 中 Markdown。

调用者还须查项目配置和工具脚本对旧文档路径的依赖。范围外 Markdown/JSON 引用文件用重复的 `--include relative/path.json` 显式加入；扫描、预览、执行须保持同样参数。源码、YAML、插件数据库和动态表达式不自动修改；发现这些依赖时先人工给出兼容方案，不宣称工具已覆盖整个仓库。

## 2. 逐文件决策

在目标范围外保存 decisions.json。每个旧结构文件必须有明确处置；标准目录内文件默认保留。例子只演示格式，不能直接套到未知正文：

```json
{
  "files": {
    "docs/adr/cache.md": {
      "action": "move",
      "to": "docs/engineering/adr/cache.md",
      "reason": "正文记录缓存架构决策、备选方案及后果"
    },
    "docs/README.md": {
      "action": "retire",
      "redirect": "docs/README.md",
      "reason": "用新合同导航替换旧导航",
      "evidence": "已逐段核验，仅有目录索引，无业务正文和独有历史结论"
    }
  },
  "directories": {"docs/adr": "docs/engineering/adr"}
}
```

| 动作 | 含义 |
|---|---|
| keep | 原位保留；reason 说明依据。旧结构中的资料不能以 keep 留下两套目录 |
| move | 按 to 移入新域，保留正文；明确 reason，不支持语义重写 |
| retire | 仅用于人工核验过的旧导航/空模板；evidence 记录核验，redirect 指向存在的替代文件；原件留在外部备份 |

directories 是明确审阅的目录引用映射，不决定文件分类。每个文件仍单独决策；若旧目录拆分成多个去处，不得随意指定统一目标。配置里的旧目录引用要由 Agent 确定其职责后处理。

同目标、相同迁移后字节可归并，清单保留所有来源；同名差异一律阻断。需要语义合并时先备份并由用户审阅合并正文，再重新扫描；工具不会拼接或删减段落。旧导航有独有正文时先迁到合适的内容文件，不把它作为空模板退役。

## 3. 审阅预览

```bash
python3 -B scripts/docs_migrate.py --target /path/to/project --decisions /path/to/decisions.json
```

`--decisions` 加载逐文件决策，只生成预览。输出包含 files（来源、目标、动作、依据、合并来源、前后哈希）、create/update/remove、将清理的空目录与 fingerprint。Agent 结合原文检查所有变更；存在歧义、未分类、同名冲突或未知引用时先解决，再预览。

fingerprint 绑定目标路径、所有扫描文件字节、目录、决策、入口范围及文件权限。它只防漂移，不证明用户批准。真实项目执行前需展示具体移除项与备份位置并取得明确授权；不能自己复制指纹伪装授权。

## 4. 批准后执行

```bash
python3 -B scripts/docs_migrate.py --target /path/to/project --decisions /path/to/decisions.json --apply --approve FINGERPRINT --backup /path/to/new-external-backup
```

`--apply` 开启迁移，`--approve` 必须是已获批准的同一预览指纹；`--backup` 必须是不存在、位于目标范围外的目录。默认 `--agent both`；可选 codex、claude、none，预览和执行保持一致。none 不新增路由规则，但扫描范围内已有入口的旧路径仍会修复。

程序先保存并回读全部范围内原件，核对哈希，再原子替换单个文件。原始状态和预期产物分别在备份 original、expected 中，record.json 记录前后清单、来源和事务状态。备份可能含项目私有内容，不随 Skill 或 Git 仓库发布。

搬迁完成后才删除已备份的旧文件，空的旧目录用 rmdir 清理；非空目录不强删。目标 .aef/docs-migration.json 保存执行收据与外部备份指针。保持备份可用，勿手动编辑机器记录。

## 5. 核验与重复调用

```bash
python3 -B scripts/docs_migrate.py --target /path/to/project --verify /path/to/new-external-backup
```

该命令核验备份原件、迁移结果文件哈希及目录；再按 [README 检查命令](../README.md) 运行初始化 CLI 的 --check，核验标准导航与入口合同。迁移构建计划时检查普通 Markdown 本地链接、引用定义、静态 docs 路径和 JSON 路径字段。新项目快照未变化时重复同一决策返回 already_migrated，不再次写入；后续新增内容用路由功能，若再次迁移须重新审阅新决策。

JSON 只更新明确的路径键，如 path、paths、evidence、evidence_ref、source、target，或以 _path/_paths/_dir/_root/_ref 结尾的字段；status、decision、actor 等其他值保持不变。未知字段残留旧路径会阻断。路径键中的审批证据链接可随文件移动，但审批人的身份、结论和状态不变。

Markdown 锚点保留但不验证标题存在；外部 URL 不联网验证；HTML、Obsidian 短名链接、动态代码表达式与二进制内部引用不在自动解析范围。Agent 应先识别这些格式并提出处理方案，不据普通链接检查声称所有外部系统已兼容。

## 6. 失败恢复

```bash
python3 -B scripts/docs_migrate.py --target /path/to/project --recover /path/to/new-external-backup
```

`--recover` 默认输出恢复预览。核对后，经用户批准再加 `--apply --approve RECOVERY_FINGERPRINT`。恢复指纹与迁移指纹不同；恢复会还原原件、移除本次新增文件并恢复目录。

迁移和恢复都要求暂停并发写入。每个文件采用原子替换，但整批不是文件系统事务；中断或断电后保留现场，用备份预览恢复，不自动删除。若有人工新改动、新资料、备份损坏或不明文件丢失，恢复停止；先另行保存并审阅差异。文件内容和原文件权限可恢复，时间戳、扩展属性、ACL 及空目录权限不做精确复原保证。

迁移后旧 adapter、harness、生命周期 CLI 不一定支持新布局。保留这一限制，调整旧运行时前另做工程评估；文档迁移不改变阶段、Gate 或审批事实。
