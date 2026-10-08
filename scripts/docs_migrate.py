"""已有项目文档迁移：默认扫描，决策预览、备份执行和恢复均显式选择。"""
import argparse
import json
import sys
from pathlib import Path
from layout import encode
from safe_files import target_path
from migration_plan import prepare, scan
from migration_store import execute, recover, verify


def main():
    """统一 JSON 输出，不捕获为成功或替用户批准。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', required=True)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--decisions', help='含 files 与 directories 的 JSON 决策文件')
    action.add_argument('--recover', help='已验证的迁移备份目录')
    action.add_argument('--verify', help='核验备份及迁移结果')
    parser.add_argument('--include', action='append', default=[], help='范围外 Markdown/JSON 引用文件的项目相对路径')
    parser.add_argument('--agent', choices=['none','codex','claude','both'], default='both')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--approve', help='用户明确批准的同一预览指纹')
    parser.add_argument('--backup', help='全新的外部备份目录')
    args = parser.parse_args()
    try:
        root = target_path(args.target)
        if not root.is_dir():
            raise ValueError('迁移目标须为已有项目；新项目使用 docs_init.py')
        if args.recover:
            result = recover(root, args.recover, args.apply, args.approve)
        elif args.verify:
            if args.apply or args.approve:
                raise ValueError('验证为只读动作')
            result = verify(root, args.verify)
        elif args.decisions:
            decision_path = Path(args.decisions).expanduser()
            if not decision_path.is_file() or decision_path.is_symlink():
                raise ValueError('决策文件必须为普通 JSON 文件')
            plan = prepare(root, json.loads(decision_path.read_text(encoding='utf-8')), args.agent, args.include)
            result = execute(root, plan, args.backup, args.approve) if args.apply else plan['report']
        else:
            if args.apply or args.approve or args.backup:
                raise ValueError('扫描不接受写入；先提供逐文件决策')
            result = scan(root, args.include)
        print(encode(result))
        return 0
    except (ValueError, OSError, UnicodeError, TypeError, KeyError) as error:
        print(encode({'status': 'blocked', 'error': str(error)}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
