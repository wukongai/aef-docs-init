"""由显式逐文件决策生成完整迁移预览，不写目标。"""
import json
import re
from pathlib import PurePosixPath
from layout import RULE, directories, encode, load_contract, render
from safe_files import child
from migration_inventory import RECEIPT, digest, hashes, relative, snapshot
from migration_refs import rewrite_json, rewrite_markdown, validate_references


def standard(path):
    """目标必须落入合同静态目录；禁止留存旧顶层结构。"""
    if path in ('docs/README.md', 'docs/constitution.md'):
        return True
    return any(path.startswith(directory + '/') for directory in directories(load_contract()) if directory != 'docs')


def scan(root, extra=()):
    """返回完整清单和明确扫描边界，不按标题猜测语义。"""
    files, dirs, _ = snapshot(root, extra)
    return {'status': 'scan', 'files': [{'source': name, 'sha256': digest(data), 'classification': 'standard' if standard(name) else 'needs_review' if name.startswith('docs/') else 'reference'} for name, data in files.items()], 'directories': dirs,
            'scope': ['docs/**', '.aef/**/*.json', 'README.md', 'AGENTS.md', 'CLAUDE.md', '.claude/rules/**/*.md', '.agents/rules/**/*.md', *extra],
            'next': '逐文件审阅正文，填写 files 决策和 directories 引用映射；范围外配置用 --include 声明。', 'written': []}


def prepare(root, decisions, agent='both', extra=()):
    """以完整前后快照绑定指纹；不确定、冲突和引用缺口整批阻断。"""
    before, dirs, modes = snapshot(root, extra)
    if not isinstance(decisions, dict) or not isinstance(decisions.get('files'), dict):
        raise ValueError('决策格式需包含 files 对象')
    decision_hash = digest(encode({'decisions': decisions, 'agent': agent, 'extra': sorted(extra)}).encode())
    if RECEIPT in before:
        receipt = json.loads(before[RECEIPT])
        if receipt.get('decisions_hash') == decision_hash:
            current = hashes({k: v for k, v in before.items() if k != RECEIPT})
            if current == receipt.get('after_hashes') and dirs == receipt.get('after_dirs'):
                return {'report': {'status': 'already_migrated', 'written': [], 'backup': receipt['backup']}}
            raise ValueError('已迁移项目随后变化；请重新扫描并提供新决策，不复用旧计划')
    choices, mappings, rows = decisions['files'], {}, []
    generated = {name: text.encode() for name, text in render(agent).items()}
    unknown = set(choices) - set(before)
    if unknown:
        raise ValueError('决策源不存在：' + ', '.join(sorted(unknown)))
    moves = {}
    for name, data in before.items():
        if name == RECEIPT:
            continue
        decision = choices.get(name)
        needs = name.startswith('docs/') and (not standard(name) or (name in generated and data != generated[name]))
        if decision is None:
            if needs:
                raise ValueError('未分类或导航冲突，需明确审阅：' + name)
            decision = {'action': 'keep', 'reason': '已在合同域内，或属于原位引用文件'}
        if not isinstance(decision, dict) or not str(decision.get('reason', '')).strip():
            raise ValueError('缺少分类依据：' + name)
        action = decision.get('action')
        target = name if action == 'keep' else decision.get('to') if action == 'move' else decision.get('redirect')
        if action not in ('keep', 'move', 'retire'):
            raise ValueError('未知处置动作：' + name)
        relative(target)
        child(root, target)
        if name.startswith('docs/'):
            if not standard(target):
                raise ValueError('目标不在新目录合同内：' + target)
        elif action != 'keep':
            raise ValueError('配置和入口仅允许原位路径修复：' + name)
        if action == 'retire' and not str(decision.get('evidence', '')).strip():
            raise ValueError('退役导航/空模板必须提供核验 evidence：' + name)
        moves[name] = (target, action)
        if target != name:
            mappings[name] = target
        rows.append({'source': name, 'target': target, 'action': action, 'reason': decision['reason'], 'evidence': decision.get('evidence'), 'before_sha256': digest(data)})
    directory_map = decisions.get('directories', {})
    if not isinstance(directory_map, dict):
        raise ValueError('directories 必须是显式目录映射')
    for old, new in directory_map.items():
        relative(old)
        relative(new)
        if old not in dirs or not old.startswith('docs/') or not standard(new + '/index.md'):
            raise ValueError('目录映射不属于现有 docs 与新合同：' + old)
        if new == old or new.startswith(old + '/'):
            raise ValueError('目录迁移不能映射到自身或其子目录')
        mappings[old] = new
        for name, (target, action) in moves.items():
            if name.startswith(old + '/') and target.startswith(old + '/'):
                raise ValueError('目录映射下仍有保留在旧结构的文件：' + name)
    after, owners = {}, {}
    for name, (target, action) in moves.items():
        if action == 'retire':
            continue
        data = before[name]
        if name.endswith(('.md', '.json')):
            text = data.decode('utf-8')
            text = rewrite_markdown(text, name, target, mappings) if name.endswith('.md') else rewrite_json(text, mappings)
            data = text.encode('utf-8')
        if target in after and after[target] != data:
            raise ValueError('同名内容冲突，需人工合并或更换目标：' + target)
        after[target] = data
        owners.setdefault(target, []).append(name)
    for name, data in generated.items():
        child(root, name)
        if name in ('AGENTS.md', 'CLAUDE.md') and name in after:
            text = after[name].decode()
            pattern = r'<!-- aef-docs-routing:v1 -->[\s\S]*?<!-- /aef-docs-routing:v1 -->\n?'
            if '<!-- aef-docs-routing:v1 -->' in text and not re.search(pattern, text):
                raise ValueError('Agent 路由段损坏：' + name)
            data = (re.sub(pattern, lambda _: RULE, text) if re.search(pattern, text) else text + '\n\n' + RULE).encode()
        elif name in after and after[name] != data and name != '.aef/docs-layout.json':
            raise ValueError('新导航与保留正文冲突，需显式迁出或退役：' + name)
        after[name] = data
    for row in rows:
        if row['target'] not in after:
            raise ValueError('退役替代目标不存在：' + row['target'])
        row['after_sha256'] = digest(after[row['target']])
        row['merged_sources'] = owners.get(row['target'], [])
    validate_references(root, after, mappings)
    output_dirs = set()
    for name in after:
        output_dirs.update(str(p) for p in PurePosixPath(name).parents if str(p) != '.')
        path = child(root, name)
        if path.exists() and path.is_dir():
            raise ValueError('文件目标与现有目录冲突：' + name)
    if set(after) & output_dirs:
        raise ValueError('文件与目录角色冲突：' + ', '.join(sorted(set(after) & output_dirs)))
    obsolete = [name for name in dirs if name.startswith('docs/') and name not in output_dirs]
    final_dirs = sorted((set(dirs) - set(obsolete)) | output_dirs)
    payload = {'target': str(root), 'before': hashes(before), 'directories': dirs, 'after': hashes(after), 'final_directories': final_dirs, 'decisions': decisions, 'agent': agent, 'extra': sorted(extra), 'modes': modes}
    fingerprint = digest(encode(payload).encode())
    report = {'status': 'preview', 'fingerprint': fingerprint, 'files': rows, 'create': sorted(set(after) - set(before)), 'update': sorted(k for k in after if k in before and after[k] != before[k]), 'remove': sorted(set(before) - set(after)), 'remove_empty_directories': obsolete, 'written': [], 'runtime_compatibility': 'not_verified'}
    return {'report': report, 'before': before, 'after': after, 'before_dirs': dirs, 'after_dirs': final_dirs, 'modes': modes, 'extra': list(extra), 'decisions_hash': decision_hash}
