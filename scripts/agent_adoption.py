"""已有入口的外部备份、漂移核对与有界恢复；不删除新增文档。"""
import hashlib
import json
import stat
from layout import encode, RULE
from safe_files import child, target_path, regular_text
from entry_coexist import ENTRIES, append_rule
from migration_store import atomic

SCHEMA = 'aef-docs-agent-backup/v1'


def digest(data):
    """以完整字节计算摘要，保留 CRLF 等原文差异。"""
    return hashlib.sha256(data).hexdigest()


def adoption_preview(root, files, states):
    """展示采用范围、原件摘要与实际追加正文，便于批准具体结果。"""
    return {name: {'before_sha256': digest(regular_text(child(root, name)).encode()),
                   'after_sha256': digest(files[name].encode()), 'append': RULE}
            for name, state in states.items() if state == 'update'}


def prepare_backup(root, files, states, raw, fingerprint):
    """先完整备份和回读，随后复核原入口未变化，任何失败均不得改目标。"""
    names = sorted(name for name, state in states.items() if state == 'update')
    if not names:
        return None, None
    if not raw:
        raise ValueError('采用旧入口必须指定外部全新备份目录 --backup')
    backup = target_path(raw)
    if backup.exists() or backup == root or root in backup.parents or backup in root.parents:
        raise ValueError('备份必须是目标范围外的全新目录')
    entries = {}
    for name in names:
        path = child(root, name)
        before = regular_text(path).encode()
        if append_rule(before.decode()) != files[name]:
            raise ValueError('入口在预检后发生变化，请重新预览：' + name)
        entries[name] = {'before_sha256': digest(before), 'after_sha256': digest(files[name].encode()),
                         'mode': stat.S_IMODE(path.stat().st_mode)}
    record = {'schema': SCHEMA, 'target': str(root), 'fingerprint': fingerprint,
              'status': 'prepared', 'entries': entries}
    backup.mkdir(mode=0o700, parents=True)
    for name in names:
        before = regular_text(child(root, name)).encode()
        if digest(before) != entries[name]['before_sha256']:
            raise ValueError('备份期间入口发生变化；目标未写入')
        for category, data in [('original', before), ('expected', files[name].encode())]:
            path = child(backup, category + '/' + name)
            atomic(path, data, 0o600)
            if regular_text(path).encode() != data:
                raise ValueError('备份回读核验失败，目标未写入')
    atomic(backup / 'record.json', encode(record).encode(), 0o600)
    for name in names:
        if digest(regular_text(child(root, name)).encode()) != entries[name]['before_sha256']:
            raise ValueError('备份后入口漂移；目标未写入；备份：' + str(backup))
    return backup, record


def update_entry(root, name, content, backup, record):
    """每次原子替换前核对原字节与模式；异常保留外部恢复指针。"""
    if name not in ENTRIES or backup is None:
        raise ValueError('未获备份保护的入口更新')
    path = child(root, name)
    entry = record['entries'][name]
    if digest(regular_text(path).encode()) != entry['before_sha256'] or stat.S_IMODE(path.stat().st_mode) != entry['mode']:
        raise ValueError('入口写前漂移；恢复备份：' + str(backup))
    atomic(path, content.encode(), entry['mode'])
    if digest(regular_text(child(root, name)).encode()) != entry['after_sha256']:
        raise ValueError('入口写后核验失败；恢复备份：' + str(backup))


def read_backup(root, raw):
    """恢复白名单仅含两种根入口；不能通过篡改记录扩展为正文写入。"""
    backup = target_path(raw)
    if backup == root or root in backup.parents or backup in root.parents:
        raise ValueError('备份必须位于目标范围外')
    record = json.loads(regular_text(child(backup, 'record.json')))
    if record.get('schema') != SCHEMA or record.get('target') != str(root):
        raise ValueError('入口备份格式或目标归属不匹配')
    entries = record.get('entries')
    if not isinstance(entries, dict) or not entries or set(entries) - ENTRIES:
        raise ValueError('入口恢复记录越出允许范围')
    for name, entry in entries.items():
        before = regular_text(child(backup, 'original/' + name)).encode()
        after = regular_text(child(backup, 'expected/' + name)).encode()
        if digest(before) != entry['before_sha256'] or digest(after) != entry['after_sha256'] or append_rule(before.decode()).encode() != after:
            raise ValueError('入口备份损坏或恢复记录不符合追加合同')
        if type(entry['mode']) is not int or not 0 <= entry['mode'] <= 0o777:
            raise ValueError('入口备份权限无效')
    return backup, record


def recover(root, raw, apply=False, approved=None):
    """恢复也先预览并绑定当前入口；人工差异绝不被覆盖。"""
    backup, record = read_backup(root, raw)
    current = {}
    for name, entry in record['entries'].items():
        path = child(root, name)
        current[name] = {'sha256': digest(regular_text(path).encode()), 'mode': stat.S_IMODE(path.stat().st_mode)}
        if current[name]['sha256'] not in (entry['before_sha256'], entry['after_sha256']) or current[name]['mode'] != entry['mode']:
            raise ValueError('恢复遇到人工修改或权限漂移：' + name)
    fingerprint = digest(encode({'backup': str(backup), 'record': record, 'current': current}).encode())
    result = {'status': 'recovery_preview', 'fingerprint': fingerprint, 'restore': sorted(current),
              'backup': str(backup), 'written': [], 'created_navigation_preserved': True}
    if not apply:
        return result
    if approved != fingerprint:
        raise ValueError('恢复需要批准同一恢复预览')
    for name, entry in record['entries'].items():
        path = child(root, name)
        if digest(regular_text(path).encode()) != current[name]['sha256'] or stat.S_IMODE(path.stat().st_mode) != current[name]['mode']:
            raise ValueError('恢复写前入口漂移；保留备份与现场')
        before = regular_text(child(backup, 'original/' + name)).encode()
        atomic(path, before, entry['mode'])
        if digest(regular_text(child(root, name)).encode()) != entry['before_sha256']:
            raise ValueError('恢复后核验失败；保留备份与现场')
        result['written'].append(name)
    result['status'] = 'recovered'
    return result
