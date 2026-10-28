"""可恢复迁移事务：先备份回读，再原子替换每个文件。"""
import json
import os
import tempfile
from pathlib import Path
from layout import encode
from safe_files import child, target_path
from migration_inventory import RECEIPT, digest, hashes, read_file, snapshot


def atomic(path, data, mode=0o644):
    """同目录临时文件落盘后替换；不会截断原文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.aef-write-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def record_write(backup, record):
    """事务记录独立原子保存。"""
    atomic(backup / 'record.json', encode(record).encode(), 0o600)


def read_record(root, raw):
    """核验备份归属、所有原件和预期产物，损坏时关闭恢复入口。"""
    backup = target_path(raw)
    if backup == root or root in backup.parents or backup in root.parents:
        raise ValueError('备份必须位于目标范围外')
    record = json.loads(read_file(backup, 'record.json'))
    if record.get('schema') != 'aef-docs-migration-backup/v1' or record.get('target') != str(root):
        raise ValueError('备份格式或项目归属不匹配')
    for category, key in (('original', 'before'), ('expected', 'after')):
        for name, sha in record[key].items():
            if digest(read_file(backup, category + '/' + name)) != sha:
                raise ValueError('备份哈希损坏：' + name)
    return backup, record


def verify(root, raw):
    """核对迁移后全范围哈希、目录与备份原件。"""
    backup, record = read_record(root, raw)
    files, dirs, _ = snapshot(root, record['extra'])
    if hashes(files) != record['after'] or dirs != record['after_dirs']:
        raise ValueError('迁移后文件清单、哈希或目录发生漂移')
    return {'status': 'verified', 'backup': str(backup), 'files': len(files), 'trace': record['trace'], 'runtime_compatibility': 'not_verified'}


def execute(root, plan, raw_backup, approved):
    """批准仅匹配既有预览；备份核验成功才开始改目标。"""
    report = plan['report']
    if report['status'] == 'already_migrated':
        return report
    if approved != report['fingerprint']:
        raise ValueError('缺少同一预览批准或指纹漂移')
    if not raw_backup:
        raise ValueError('必须指定目标范围外的新备份目录 --backup')
    backup = target_path(raw_backup)
    if backup.exists() or root == backup or root in backup.parents or backup in root.parents:
        raise ValueError('备份必须是目标范围外的全新目录')
    after = dict(plan['after'])
    receipt = {'schema': 'aef-docs-migration/v1', 'fingerprint': approved, 'decisions_hash': plan['decisions_hash'], 'after_hashes': hashes(after), 'after_dirs': plan['after_dirs'], 'backup': str(backup), 'runtime_compatibility': 'not_verified'}
    after[RECEIPT] = encode(receipt).encode()
    record = {'schema': 'aef-docs-migration-backup/v1', 'target': str(root), 'status': 'preparing', 'fingerprint': approved, 'before': hashes(plan['before']), 'after': hashes(after), 'before_dirs': plan['before_dirs'], 'after_dirs': plan['after_dirs'], 'modes': plan['modes'], 'extra': plan['extra'], 'trace': report['files']}
    backup.mkdir(mode=0o700, parents=True)
    for category, files in (('original', plan['before']), ('expected', after)):
        for name, data in files.items():
            path = child(backup, category + '/' + name)
            atomic(path, data, 0o600)
            if read_file(backup, category + '/' + name) != data:
                raise ValueError('备份回读验证失败，目标未写入')
    record['status'] = 'prepared'
    record_write(backup, record)
    current, dirs, modes = snapshot(root, plan['extra'])
    if current != plan['before'] or dirs != plan['before_dirs'] or modes != plan['modes']:
        raise ValueError('备份期间目标变化，目标未写入；需重新预览')
    written = []
    try:
        record['status'] = 'applying'
        record_write(backup, record)
        for name, data in after.items():
            if plan['before'].get(name) == data:
                continue
            path = child(root, name)
            actual = read_file(root, name) if path.exists() else None
            if actual != plan['before'].get(name):
                raise ValueError('写入前文件发生并发变化：' + name)
            atomic(path, data, plan['modes'].get(name, 0o644))
            written.append(name)
        for name in sorted(set(plan['before']) - set(after)):
            if read_file(root, name) != plan['before'][name]:
                raise ValueError('退役前源文件发生变化：' + name)
            child(root, name).unlink()
            written.append(name)
        for name in sorted(set(plan['before_dirs']) - set(plan['after_dirs']), key=lambda p: len(Path(p).parts), reverse=True):
            child(root, name).rmdir()
        verify(root, backup)
        record['status'] = 'applied'
        record_write(backup, record)
        return {'status': 'applied', 'backup': str(backup), 'fingerprint': approved, 'written': written, 'files': report['files'], 'runtime_compatibility': 'not_verified'}
    except Exception as error:
        record['status'] = 'failed'
        record['error'] = str(error)
        record_write(backup, record)
        raise ValueError('迁移未完成；备份与恢复记录：' + str(backup) + '；原因：' + str(error)) from error


def recover(root, raw, apply=False, approved=None):
    """只恢复仍为原值/计划值的文件，拒绝覆盖迁移后的人工变更。"""
    backup, record = read_record(root, raw)
    current, dirs, _ = snapshot(root, record['extra'])
    states = hashes(current)
    allowed_names = set(record['before']) | set(record['after'])
    if set(states) - allowed_names:
        raise ValueError('恢复范围出现新增资料；请先另行保存，不覆盖')
    for name in allowed_names:
        if states.get(name) not in (record['before'].get(name), record['after'].get(name)):
            raise ValueError('恢复遇到人工修改或不明丢失：' + name)
    if set(dirs) - set(record['before_dirs']) - set(record['after_dirs']):
        raise ValueError('恢复范围出现新增目录')
    fingerprint = digest(encode({'backup': str(backup), 'record': record, 'current': states, 'dirs': dirs}).encode())
    if not apply:
        return {'status': 'recovery_preview', 'fingerprint': fingerprint, 'restore': sorted(record['before']), 'remove_created': sorted(set(states) - set(record['before'])), 'written': []}
    if approved != fingerprint:
        raise ValueError('恢复需要批准同一恢复预览')
    for name in record['before']:
        atomic(child(root, name), read_file(backup, 'original/' + name), record['modes'].get(name, 0o644))
    for name in sorted(set(states) - set(record['before'])):
        child(root, name).unlink()
    for name in sorted(set(dirs) - set(record['before_dirs']), key=lambda p: len(Path(p).parts), reverse=True):
        child(root, name).rmdir()
    for name in record['before_dirs']:
        child(root, name).mkdir(parents=True, exist_ok=True)
    actual, actual_dirs, _ = snapshot(root, record['extra'])
    if hashes(actual) != record['before'] or actual_dirs != record['before_dirs']:
        raise ValueError('恢复核验失败，保留备份和现场')
    record['status'] = 'recovered'
    record_write(backup, record)
    return {'status': 'recovered', 'backup': str(backup), 'files': len(actual)}
