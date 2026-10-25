"""非覆盖文件计划：只读预检、指纹批准与排他新增。"""
import hashlib
from pathlib import Path
from layout import encode, RULE
from entry_coexist import ENTRIES, append_rule, baseline_block, has_rule, preserve_navigation


def target_path(raw):
    """目标及父路径禁止链接与父目录穿越。"""
    path = Path(raw).expanduser()
    if ".." in path.parts:
        raise ValueError("目标路径穿越")
    if not path.is_absolute():
        path = Path.cwd() / path
    if any(node.is_symlink() for node in [path, *path.parents]):
        raise ValueError("目标或父目录为符号链接，请使用已核实真实路径")
    if path == Path(path.anchor) or (path.exists() and not path.is_dir()):
        raise ValueError("目标必须是非根目录")
    return path


def child(root, relative):
    """不跟随内部链接，拒绝父目录文件。"""
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("相对路径越界")
    result = root / path
    for node in [result, *list(result.parents)[:len(path.parts)]]:
        if node.is_symlink():
            raise ValueError("目标内部包含链接")
        if node != result and node.exists() and not node.is_dir():
            raise ValueError("父路径不是目录")
    return result


def regular_text(path):
    """拒绝非常规文件和硬链接，再按原字节解码，绝不转换换行。"""
    if not path.is_file():
        raise ValueError("预期普通文件：" + path.name)
    if path.stat().st_nlink != 1:
        raise ValueError("不读取硬链接文件：" + path.name)
    return path.read_bytes().decode("utf-8")


def plan(root, files, adopt_agent=False):
    """绑定所有预期文件、目标和实际状态；任何冲突阻断。"""
    files = dict(files)
    states = {}
    for relative, content in files.items():
        path = child(root, relative)
        if path.exists():
            current = regular_text(path)
            if relative in ENTRIES:
                baseline_block(current)
                if has_rule(current):
                    files[relative] = current
                elif current != content and adopt_agent:
                    files[relative] = append_rule(current)
                    states[relative] = "update"
                    continue
                elif current != content:
                    raise ValueError("已有入口差异；需显式 --adopt-agent 预览采用：" + relative)
            elif preserve_navigation(relative, current, content):
                files[relative] = current
            elif current != content:
                raise ValueError("已有差异，整批未写入：" + relative)
        states[relative] = "unchanged" if path.exists() else "create"
    fingerprint = hashlib.sha256(encode({"target": str(root), "files": files, "states": states}).encode()).hexdigest()
    return files, states, fingerprint


def apply(root, files, states, written, backup=None, fingerprint=None):
    """新增使用排他写；更新先备份，失败保留现场及明确恢复指针。"""
    from agent_adoption import prepare_backup, update_entry
    saved, record = prepare_backup(root, files, states, backup, fingerprint)
    try:
        for relative, content in files.items():
            if states[relative] == "unchanged":
                continue
            if states[relative] == "update":
                update_entry(root, relative, content, saved, record)
                written.append(relative)
                continue
            path = child(root, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as handle:
                written.append(relative)
                handle.write(content)
    except (ValueError, OSError) as error:
        if saved:
            raise ValueError('采用未完成；入口恢复备份：' + str(saved) + '；原因：' + str(error)) from error
        raise
    return str(saved) if saved else None
