"""独立文档初始化、持续路由与检查 CLI；默认只读。"""
import argparse
import json
import sys
from layout import encode, load_contract, render, route
from safe_files import target_path, child, regular_text, plan, apply
from agent_adoption import adoption_preview, recover
from entry_coexist import NAVIGATION, baseline_block


def main():
    """执行显式动作，统一返回可审计 JSON 与退出码。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--agent", choices=["none", "codex", "claude", "both"], default=None)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true")
    group.add_argument("--check", action="store_true")
    group.add_argument("--route", metavar="文档类型")
    parser.add_argument("--approve", help="明确用户批准的同一预览指纹")
    parser.add_argument("--name", help="需求、变更、能力、周期、版本或文档名称")
    parser.add_argument("--validate-path", help="只校验提供路径是否匹配类型与名称")
    parser.add_argument("--adopt-agent", action="store_true", help="显式预览在已有所选根入口末尾追加文档规则")
    parser.add_argument("--backup", help="更新已有入口时使用的目标外全新备份目录")
    parser.add_argument("--recover-agent", help="入口采用备份；默认只预览恢复，不删除新增导航")
    args = parser.parse_args()
    written = []
    try:
        root = target_path(args.target)
        if args.recover_agent:
            if args.agent or args.adopt_agent or args.backup or args.check or args.route or args.name or args.validate_path:
                raise ValueError("入口恢复不可与初始化、路由或检查选项混用")
            print(encode(recover(root, args.recover_agent, args.apply, args.approve)))
            return 0
        if args.backup and not args.apply:
            raise ValueError("--backup 仅用于批准后的采用写入")
        saved = child(root, ".aef/docs-layout.json")
        contract = load_contract()
        agent = args.agent or "both"
        if saved.exists():
            stored = json.loads(regular_text(saved))
            if not isinstance(stored, dict) or stored.get("schema") != contract["schema"] or stored.get("paths") != contract["paths"]:
                raise ValueError("已存目录合同漂移，需评审迁移")
            agent = args.agent or stored.get("agent", "both")
        if args.route:
            if args.approve or args.agent or args.adopt_agent or args.backup:
                raise ValueError("路由只读，不接受批准或入口选项")
            path = route(contract, args.route, args.name)
            child(root, path)
            if args.validate_path is not None and args.validate_path != path:
                raise ValueError("给定路径与该文档类型的落点不一致；正确路径：" + path)
            print(encode({"status": "path_valid" if args.validate_path else "route", "kind": args.route, "path": path, "written": []}))
            return 0
        if args.name or args.validate_path:
            raise ValueError("名称和路径校验必须与 --route 一起使用")
        if args.check and args.adopt_agent:
            raise ValueError("--check 只验证现状，不执行入口采用")
        files, states, fingerprint = plan(root, render(agent), args.adopt_agent)
        adoptions = adoption_preview(root, files, states)
        external = sorted(name for name in NAVIGATION if name in files and baseline_block(files[name]))
        if args.check and any(state != "unchanged" for state in states.values()):
            raise ValueError("缺少目录导航、机器合同或入口")
        if args.apply:
            if args.approve != fingerprint:
                raise ValueError("未批准同一预览或预览已漂移")
            backup = apply(root, files, states, written, args.backup, fingerprint)
            plan(root, render(agent))
        else:
            backup = None
        print(encode({"status": "applied" if args.apply else "checked" if args.check else "preview", "fingerprint": fingerprint, "files": states, "written": written, "agent_projection": agent, "utility_claim": False, "agent_adoptions": adoptions, "external_blocks_unverified": external, "backup": backup, "recovery": {"action": "--recover-agent", "backup": backup} if backup else None}))
        return 0
    except (ValueError, OSError, UnicodeError, TypeError, KeyError) as error:
        print(encode({"status": "blocked", "error": str(error), "written": written}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
