# Skill 与目标文档结构

## 独立 Skill

入口 SKILL.md 按初始化、落点查询、检查分流；scripts/docs_init.py 是公开 CLI，layout.py 管单一合同与渲染，safe_files.py 管安全写入。templates/directory-contract.json 是完整类型映射。references 解释分类，tests 固化真实文件行为。无需 AEF owner 仓库或应用技术栈。

## 初始化后的完整静态目录

包括 docs 根在内，共 51 个文档目录；每个目录都有 README.md，以下树省略重复 README。默认另加 .aef/docs-layout.json 和两个可选 Agent 入口；不生成业务工程目录。ideas.md、board.md 及业务正文只登记落点，实际需要时才写。

```text
└── docs/
    ├── product/
    │   ├── research/
    │   ├── requirements/
    │   ├── prd/
    │   └── releases/
    ├── project/
    │   ├── tasks/
    │   ├── sprints/
    │   ├── lifecycle/
    │   ├── meetings/
    │   ├── logs/
    │   └── handoffs/
    ├── engineering/
    │   ├── architecture/
    │   ├── research/
    │   ├── adr/
    │   ├── specs/
    │   ├── changes/
    │   ├── api/
    │   ├── data/
    │   ├── standards/
    │   └── maintenance/
    │       ├── environment/
    │       ├── runbooks/
    │       ├── monitoring/
    │       ├── incidents/
    │       └── migrations/
    ├── business/
    │   ├── marketing/
    │   │   ├── campaigns/
    │   │   └── materials/
    │   ├── sales/
    │   │   └── templates/
    │   └── metrics/
    ├── customer-success/
    │   ├── beta/
    │   ├── onboarding/
    │   ├── engagement/
    │   ├── feedback/
    │   ├── support/
    │   └── reviews/
    └── knowledge/
        ├── team/
        │   ├── onboarding/
        │   ├── learning/
        │   ├── tutorials/
        │   └── explanations/
        ├── users/
        │   └── guides/
        └── references/
```

## 全部内容落点

以下 73 个文档类型完整登记。普通叶子文档按实际工作撰写，不填充假业务内容。尖括号表示实例：固定父目录已经建立，实例在需求、版本或变更真正发生时创建。同一文件可承载多个职责；需求发现与用户故事共用一份 story，故事卡 JSON 仅为按需机器接口。PRD 用于多个故事的整体产品方案。

| 类型 | 对应路径 |
|---|---|
| 导航 | `docs/README.md` |
| 项目原则 | `docs/constitution.md` |
| 产品定位 | `docs/product/positioning.md` |
| 路线图 | `docs/product/roadmap.md` |
| 产品调研 | `docs/product/research/` |
| 点子 | `docs/product/ideas.md` |
| 需求发现 | `docs/product/requirements/<需求名>/story.md` |
| 用户故事 | `docs/product/requirements/<需求名>/story.md` |
| 故事卡 | `docs/product/requirements/<需求名>/story-card.json` |
| 产品需求文档 | `docs/product/prd/` |
| 发布导航 | `docs/product/releases/README.md` |
| 变更日志 | `docs/product/releases/CHANGELOG.md` |
| 发布记录 | `docs/product/releases/<版本>/release.md` |
| 发布说明 | `docs/product/releases/<版本>/release-notes.md` |
| 发布验证 | `docs/product/releases/<版本>/verification.md` |
| 版本回滚 | `docs/product/releases/<版本>/rollback.md` |
| 看板 | `docs/project/board.md` |
| 待办 | `docs/project/board.md` |
| 任务 | `docs/project/tasks/` |
| 迭代 | `docs/project/sprints/` |
| 生命周期 | `docs/project/lifecycle/<周期>/` |
| 风险 | `docs/project/risks.md` |
| 会议 | `docs/project/meetings/` |
| 日报 | `docs/project/logs/` |
| 周报 | `docs/project/logs/` |
| 交接 | `docs/project/handoffs/` |
| 工程导航 | `docs/engineering/README.md` |
| 架构 | `docs/engineering/architecture/` |
| 技术选型实验基线 | `docs/engineering/research/` |
| 架构决策 | `docs/engineering/adr/` |
| 生效规格 | `docs/engineering/specs/<能力名>/spec.md` |
| 变更提案 | `docs/engineering/changes/<变更名>/proposal.md` |
| 变更设计 | `docs/engineering/changes/<变更名>/design.md` |
| 拟议规格 | `docs/engineering/changes/<变更名>/spec.md` |
| 技术计划 | `docs/engineering/changes/<变更名>/plan.md` |
| 测试设计 | `docs/engineering/changes/<变更名>/testing.md` |
| 验证证据 | `docs/engineering/changes/<变更名>/verification.md` |
| 评审 | `docs/engineering/changes/<变更名>/review.md` |
| 变更附件 | `docs/engineering/changes/<变更名>/assets/` |
| 诊断 | `docs/engineering/changes/<变更名>/diagnosis.md` |
| 优化 | `docs/engineering/changes/<变更名>/optimization.md` |
| 接口 | `docs/engineering/api/` |
| 数据 | `docs/engineering/data/` |
| 规范 | `docs/engineering/standards/` |
| 环境 | `docs/engineering/maintenance/environment/` |
| 操作部署回滚手册 | `docs/engineering/maintenance/runbooks/` |
| 监控 | `docs/engineering/maintenance/monitoring/` |
| 事故 | `docs/engineering/maintenance/incidents/` |
| 迁移 | `docs/engineering/maintenance/migrations/` |
| 商业化 | `docs/business/commercialization.md` |
| 定价 | `docs/business/pricing.md` |
| 内容规划 | `docs/business/marketing/content-plan.md` |
| 活动 | `docs/business/marketing/campaigns/` |
| 营销素材 | `docs/business/marketing/materials/` |
| 销售手册 | `docs/business/sales/playbook.md` |
| 销售问答 | `docs/business/sales/faq.md` |
| 销售模板 | `docs/business/sales/templates/` |
| 商业指标 | `docs/business/metrics/` |
| 内测 | `docs/customer-success/beta/` |
| 客户接入 | `docs/customer-success/onboarding/` |
| 客户运营 | `docs/customer-success/engagement/` |
| 客户反馈 | `docs/customer-success/feedback/` |
| 客户支持 | `docs/customer-success/support/` |
| 客户复盘 | `docs/customer-success/reviews/` |
| 知识入口 | `docs/knowledge/README.md` |
| 团队入职 | `docs/knowledge/team/onboarding/` |
| 团队学习 | `docs/knowledge/team/learning/` |
| 团队教程 | `docs/knowledge/team/tutorials/` |
| 原理解释 | `docs/knowledge/team/explanations/` |
| 用户入门 | `docs/knowledge/users/getting-started.md` |
| 用户指南 | `docs/knowledge/users/guides/` |
| 用户问答 | `docs/knowledge/users/faq.md` |
| 参考资料 | `docs/knowledge/references/` |

发布相关正文归 product/releases；工程文档归 docs/engineering，不等于创建业务应用工程。README 是用途与导航，初始化不意味着业务文件已完成。

待办不带名称查看板，带名称查 tasks 中的任务正文；日志带名称自动补 -daily.md / -weekly.md 后缀。看板的列是状态，正文不随状态移动；状态以任务卡或外部看板为唯一来源，Sprint 和日志引用它。
