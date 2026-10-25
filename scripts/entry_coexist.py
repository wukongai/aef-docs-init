"""两工具各管自己的内容：显式追加入口，严格保留外部导航附加块。"""
from layout import RULE

START = '<!-- aef:baseline:start -->'
END = '<!-- aef:baseline:end -->'
NAVIGATION = {'docs/README.md', 'docs/engineering/README.md'}
ENTRIES = {'AGENTS.md', 'CLAUDE.md'}


def baseline_block(text):
    """只识别唯一完整独立行标记，不验证其中正文与实际宿主效用。"""
    if 'aef:baseline:' not in text:
        return None
    if text.count('aef:baseline:') != 2 or text.count(START) != 1 or text.count(END) != 1:
        raise ValueError('工程基线管理标记重复、未知或不完整')
    start, end = text.index(START), text.index(END)
    if start >= end or (start and text[start - 1] != '\n'):
        raise ValueError('工程基线管理标记必须按序独立成行')
    if not text[start + len(START):].startswith(('\n', '\r\n')):
        raise ValueError('工程基线开始标记必须独立成行')
    if end and text[end - 1] != '\n':
        raise ValueError('工程基线结束标记必须独立成行')
    tail = text[end + len(END):]
    if tail and not tail.startswith(('\n', '\r\n')):
        raise ValueError('工程基线结束标记必须独立成行')
    return text[start:end + len(END)]


def has_rule(text):
    """完整原规则可与人工正文共存；破损或重复旧标记不能自动采用。"""
    if 'aef-docs-routing:' not in text:
        return False
    if text.count('aef-docs-routing:') != 2 or text.count(RULE) != 1:
        raise ValueError('文档路由管理标记破损、重复或正文已变更；需人工审阅')
    return True


def append_rule(text):
    """旧入口每个字符保留，仅追加已展示的完整文档规则。"""
    baseline_block(text)
    if has_rule(text):
        raise ValueError('入口已有文档规则，不应再次采用')
    return text + ('\n' if text.endswith('\n') else '\n\n') + RULE


def preserve_navigation(relative, current, expected):
    """仅在原生成导航逐字相同且附加块位于末尾时保留另一工具内容。"""
    if relative not in NAVIGATION:
        return False
    block = baseline_block(current)
    if block is None:
        return False
    return current in (expected + block, expected + '\n' + block,
                       expected + block + '\n', expected + '\n' + block + '\n')
