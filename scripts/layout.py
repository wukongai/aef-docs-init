"""单一文档合同：完整静态目录渲染与只读落点解析。"""
import json
import re
from pathlib import Path, PurePosixPath

SOURCE = Path(__file__).resolve().parents[1] / "templates/directory-contract.json"
RULE = """<!-- aef-docs-routing:v1 -->
## 文档落点

新增或修改文档前，先读 `docs/README.md` 的类型索引；机器合同为 `.aef/docs-layout.json`。
先判断产品事实、项目执行、技术工程、商业、客户成功或知识，再选择精确类型。类型有歧义先澄清，不按标题关键词猜测。
需要确定路径时使用 aef-docs-init 的只读 route 动作；普通写作无需重新初始化。
实例名称确定后再建需求、版本、能力、变更或周期目录。写入前检查已有文件，不覆盖差异。
用户指南正文只保存在 knowledge/users；其他领域引用。任务状态只有一个来源，日志和 Sprint 引用任务。
写后按类型校验落点；初始化检查仅覆盖目录、索引、入口，不代表正文、测试或 Gate 通过。
<!-- /aef-docs-routing:v1 -->
"""
PRINCIPLES = """Product 记录产品事实和演进方向；Project 记录执行安排。发布归 product/releases，发布任务归 project/tasks。
产品五类产物：产品定义（product-definition.md）、用户与市场研究（research）、Epic/用户故事（requirements）、故事地图（story-map.md）、迭代计划（project/sprints）。
定位是产品定义的一部分，定义还包含用户、价值、商业画布与指标；同一事实只维护一份正文。已有正文先读并审阅增量，职责冲突时保留原文并确认处理方案。
点子先记 product/ideas.md；明确用户、价值与验收后形成 requirements/<需求名>/story.md，需求背景写入同一故事。详细调研归 product/research。
PRD 组织多个故事的产品方案，不要求每个故事另写 PRD。story-card.json 是按需机器接口，不要求人工重复维护。
Project 看板入口为 board.md，需求池、待办、进行中、待验收、已完成是状态；具名待办正文归 tasks，状态流转不搬文件。
任务卡或已采用的外部看板为状态唯一来源；board.md 仅作视图或链接入口，不再手工复制状态。日报、周报归 logs，以 -daily.md、-weekly.md 区分。
CHANGELOG 记录 Unreleased 和工程版本变化，不写任务进度。Plan 写技术步骤并引用任务 ID；Sprint 承载本轮目标、故事承诺、依赖与结果，可引用执行任务，Sprint 和日报不复制任务状态。
生命周期周期、版本和 Sprint 分开；阶段文档不冒充批准，机器阶段状态仍在 `.aef/lifecycle/<周期>/manifest.json`。
变更包 spec 是拟议规格；验证和评审通过后更新生效规格。debug 加 diagnosis，优化加 optimization。
通用部署/回滚手册在 engineering/maintenance/runbooks；具体版本回滚证据在 product/releases。
Wiki 以 knowledge/README 为入口；用户指南正文唯一保存于 knowledge/users，运营只引用。
学习记录讲学到什么；日报讲做了什么。产品调研与技术选型实验分开。
本文档初始化一次建立全部静态分类；带尖括号的路径是未来实例，不创建字面占位目录。
凭证、真实客户明细和工程运行日志不进入文档仓。测试代码不放 docs。旧资料保留，迁移另行评审。
目录存在只说明分类就绪，不说明产品文档已写、阶段已批准或版本已发布。
"""


def encode(value):
    """稳定编码，保持重复执行无内容漂移。"""
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def load_contract():
    """校验受分发的路径合同；只允许 docs 下的相对路径。"""
    value = json.loads(SOURCE.read_text(encoding="utf-8"))
    if value.get("schema") != "aef-docs-layout/v1" or not isinstance(value.get("paths"), dict):
        raise ValueError("文档合同格式错误")
    for path in value["paths"].values():
        if not isinstance(path, str) or not path.startswith("docs/") or "\\" in path or ".." in PurePosixPath(path).parts:
            raise ValueError("文档合同包含越界路径")
    return value


def directories(contract):
    """展开所有静态父目录，保留动态实例为索引。"""
    result = {"docs"}
    for text in contract["paths"].values():
        if "<" in text:
            base = PurePosixPath(text.split("<", 1)[0])
        else:
            base = PurePosixPath(text) if text.endswith("/") else PurePosixPath(text).parent
        result.add(str(base))
        result.update(str(parent) for parent in base.parents if str(parent) != ".")
    return sorted(result)


def table(paths):
    """生成可查类型表，表中的实例不等于已创建文档。"""
    return "| 文档类型 | 路径 |\n|---|---|\n" + "".join(f"| {kind} | `{path}` |\n" for kind, path in paths.items())


def render(agent):
    """生成全部静态目录 README、机器合同及可选根入口。"""
    if agent not in ("none", "codex", "claude", "both"):
        raise ValueError("未知 Agent 入口")
    contract = load_contract()
    files = {".aef/docs-layout.json": encode({**contract, "agent": agent})}
    for directory in directories(contract):
        paths = {k: v for k, v in contract["paths"].items() if v.startswith(directory + "/")}
        title = "项目文档总导航" if directory == "docs" else directory.removeprefix("docs/") + " 文档导航"
        body = f"# {title}\n\n本目录存放下表对应材料；按类型选择正文位置，避免重复维护。\n\n"
        body += PRINCIPLES + "\n" if directory == "docs" else "完整分类见项目 `docs/README.md`；机器索引见 `.aef/docs-layout.json`。\n\n"
        files[directory + "/README.md"] = body + table(paths)
    if agent in ("codex", "both"):
        files["AGENTS.md"] = RULE
    if agent in ("claude", "both"):
        files["CLAUDE.md"] = RULE
    return files


def route(contract, kind, name=None):
    """按精确类型返回路径，名称只允许单个安全路径组件。"""
    if kind not in contract["paths"]:
        raise ValueError("未知文档类型；请查 docs/README.md 的精确类型名")
    path = contract["paths"][kind]
    if name is not None and (not re.fullmatch(r"[\w][\w.-]{0,119}", name) or ".." in name):
        raise ValueError("实例名称必须是安全的单个名称，禁止穿越和分隔符")
    if kind == "待办" and name:
        # 具名待办复用任务正文；不带名称时查询看板入口。
        path = contract["paths"]["任务"]
    if kind in ("日报", "周报") and name:
        # 合并目录但保留类型后缀，防止同名日报和周报覆盖。
        if name.endswith(".json"):
            raise ValueError("日报、周报使用 Markdown 文件名")
        stem = name.removesuffix(".md")
        suffix = "-daily" if kind == "日报" else "-weekly"
        name = stem + ("" if stem.endswith(suffix) else suffix) + ".md"
    if "<" in path:
        if not name:
            raise ValueError("该文档类型需要 --name 指定实例名称")
        path = re.sub(r"<[^>]+>", name, path)
    elif path.endswith("/") and name:
        path += name if name.endswith((".md", ".json")) else name + ".md"
    elif name:
        raise ValueError("该类型为固定文件，不接受实例名称")
    return path
