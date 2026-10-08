"""迁移范围、路径安全与字节级快照；只读。"""
import hashlib
import json
import os
import stat
from pathlib import Path, PurePosixPath
from safe_files import child

RECEIPT = '.aef/docs-migration.json'
POLICY = json.loads((Path(__file__).resolve().parents[1] / 'templates/migration-policy.json').read_text(encoding='utf-8'))


def digest(data):
    """稳定的内容指纹。"""
    return hashlib.sha256(data).hexdigest()


def relative(value):
    """只接受规范的项目相对路径，不接受链接或替代分隔符。"""
    if not isinstance(value, str) or not value or '\\' in value or '\x00' in value:
        raise ValueError('非法相对路径')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or str(path) != value or value == '.':
        raise ValueError('相对路径越界或不规范：' + value)
    if any(part in POLICY['denied_path_names'] or any(part.startswith(prefix) for prefix in POLICY['denied_path_prefixes']) for part in path.parts):
        raise ValueError('不允许读取版本库内部或凭证文件')
    return value


def read_file(root, name):
    """读取普通文件；拒绝硬链接，避免影响未声明路径。"""
    path = child(root, relative(name))
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError('不是独立普通文件：' + name)
    return path.read_bytes()


def snapshot(root, extra=()):
    """枚举 docs 全树、.aef JSON、根文档、Agent 规则及显式引用文件。"""
    files, directories, modes = {}, set(), {}
    names = set(extra)
    for name in names:
        relative(name)
        if not name.endswith(('.md', '.json')):
            raise ValueError('额外引用文件仅支持 Markdown/JSON：' + name)
    for name in ('README.md', 'AGENTS.md', 'CLAUDE.md'):
        path = child(root, name)
        if path.exists() or path.is_symlink():
            names.add(name)
    for base in ('docs', '.aef', '.claude/rules', '.agents/rules'):
        start = child(root, base)
        if not start.exists():
            continue
        if not start.is_dir():
            raise ValueError('扫描根不是目录：' + base)
        for current, dirs, leaves in os.walk(start, followlinks=False):
            directory = Path(current)
            directories.add(directory.relative_to(root).as_posix())
            directories.update(str(p) for p in PurePosixPath(directory.relative_to(root).as_posix()).parents if str(p) != '.')
            for name in dirs + leaves:
                path = directory / name
                rel = path.relative_to(root).as_posix()
                child(root, relative(rel))
                if path.is_symlink():
                    raise ValueError('扫描范围内包含符号链接：' + rel)
            for name in leaves:
                rel = (directory / name).relative_to(root).as_posix()
                if base == 'docs' or (base == '.aef' and name.endswith('.json')) or (base.endswith('/rules') and name.endswith('.md')):
                    names.add(rel)
    for name in sorted(names):
        files[name] = read_file(root, name)
        modes[name] = stat.S_IMODE(child(root, name).stat().st_mode)
        directories.update(str(p) for p in PurePosixPath(name).parents if str(p) != '.')
    return files, sorted(directories), modes


def hashes(files):
    """清单中不输出原始正文。"""
    return {name: digest(data) for name, data in sorted(files.items())}
