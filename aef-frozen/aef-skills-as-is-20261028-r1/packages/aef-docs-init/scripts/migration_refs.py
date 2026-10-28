"""确定性文档路径修复；保留正文、锚点和非路径审批值。"""
import json
import posixpath
import re
from urllib.parse import quote, unquote, urlsplit

LINK = re.compile(r'(!?\[[^\]\n]*\]\()(?P<url><[^>\n]+>|[^\s)]+)(?P<tail>[^\n]*?\))')
DEFINITION = re.compile(r'^(\s*\[[^\]\n]+\]:\s*)(<[^>\n]+>|\S+)', re.M)
PATH = re.compile(r'(?<![\w/])(?:\./)?docs/[\w./<>\-\u0080-\uffff]+')
PATH_KEYS = {'path', 'paths', 'file', 'files', 'ref', 'refs', 'evidence', 'evidence_ref', 'source', 'target', 'docs_root'}


def mapped(path, mappings):
    """最长前缀映射，目录与文件边界严格匹配。"""
    for old in sorted(mappings, key=len, reverse=True):
        if path == old or path.startswith(old + '/'):
            return mappings[old] + path[len(old):]
    return path


def local_link(url, source):
    """解析本地 Markdown 链接；外部 URL、锚点原样保留。"""
    wrapped = url.startswith('<') and url.endswith('>')
    text = url[1:-1] if wrapped else url
    parts = urlsplit(text)
    if parts.scheme or parts.netloc or not parts.path or parts.path.startswith('/'):
        return None
    path = posixpath.normpath(posixpath.join(posixpath.dirname(source), unquote(parts.path)))
    return path, parts, wrapped


def rewrite_markdown(text, source, target, mappings):
    """移动文件时同步调整相对链接，根路径片段统一映射。"""
    def url_change(url):
        parsed = local_link(url, source)
        if parsed is None:
            return url
        path, parts, wrapped = parsed
        new_path = mapped(path, mappings)
        result = posixpath.relpath(new_path, posixpath.dirname(target) or '.')
        result = quote(result, safe='/.-_~')
        if parts.query:
            result += '?' + parts.query
        if parts.fragment:
            result += '#' + parts.fragment
        return '<' + result + '>' if wrapped else result

    # Markdown 先处理链接，随后处理项目根路径；代码块不执行，仅更新静态路径。
    text = LINK.sub(lambda m: m[1] + url_change(m['url']) + m['tail'], text)
    text = DEFINITION.sub(lambda m: m[1] + url_change(m[2]), text)
    return PATH.sub(lambda m: mapped(m[0].removeprefix('./').rstrip('/'), mappings) + ('/' if m[0].endswith('/') else ''), text)


def rewrite_json(text, mappings):
    """只更新明确路径字段；审批状态、自由描述和历史事件不改写。"""
    original = json.loads(text)

    def visit(value, key=''):
        if isinstance(value, dict):
            return {k: visit(v, k) for k, v in value.items()}
        if isinstance(value, list):
            return [visit(v, key) for v in value]
        if isinstance(value, str) and (key in PATH_KEYS or key.endswith(('_path', '_paths', '_dir', '_root', '_ref'))):
            return mapped(value.rstrip('/'), mappings) + ('/' if value.endswith('/') else '')
        return value

    result = visit(original)
    return text if result == original else json.dumps(result, ensure_ascii=False, indent=2) + '\n'


def validate_references(root, files, mappings):
    """检查可解析本地链接与遗留路径，无法安全修复时阻断。"""
    issues = []
    directories = {posixpath.dirname(name) for name in files}
    for directory in list(directories):
        while directory:
            directories.add(directory)
            directory = posixpath.dirname(directory)
    for name, data in files.items():
        if not name.endswith(('.md', '.json')):
            continue
        text = data.decode('utf-8')
        if name.endswith('.md'):
            urls = [m['url'] for m in LINK.finditer(text)] + [m[2] for m in DEFINITION.finditer(text)]
            for url in urls:
                parsed = local_link(url, name)
                if parsed is None:
                    continue
                path = parsed[0]
                if '<' in path or '>' in path:
                    continue
                if path.startswith('../') or (path not in files and path not in directories and (path.startswith('docs/') or not (root / path).exists())):
                    issues.append(name + '：无法解析本地链接 ' + url)
        for old, new in mappings.items():
            if old != new and re.search(r'(?<![\w/])' + re.escape(old) + r'(?=$|[/\s`"\]#)])', text):
                issues.append(name + '：残留旧路径，需人工处理或声明字段 ' + old)
    if issues:
        raise ValueError('引用检查未通过：' + '; '.join(issues[:12]))
