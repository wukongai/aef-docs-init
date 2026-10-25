"""通过真实 CLI 验证入口采用、外部备份与导航并存。"""
import hashlib
import json
import unittest
import test_docs

START = '<!-- aef:baseline:start -->'
END = '<!-- aef:baseline:end -->'
BLOCK = START + '\n工程基线自有导航，Docs Init 不验证正文。\n' + END + '\n'


class CoexistTests(unittest.TestCase):
    """合成临时项目；保留原回归断言与全部目录合同。"""

    setUp = test_docs.DocsTests.setUp
    run_cli = test_docs.DocsTests.run_cli
    apply = test_docs.DocsTests.apply

    def existing(self, content=None):
        """构造已有 baseline 根入口与外部备份路径。"""
        self.target.mkdir()
        text = content if content is not None else '# 人工规则\r\n\r\n' + BLOCK + '\n人工尾文\n'
        (self.target / 'AGENTS.md').write_bytes(text.encode())
        self.original = text.encode()
        self.backup = self.base / 'entry-backup'

    def adopted(self):
        """只批准 fixture 的显式入口采用计划。"""
        preview = self.run_cli('--agent', 'codex', '--adopt-agent')
        return self.run_cli('--agent', 'codex', '--adopt-agent', '--apply', '--approve', preview['fingerprint'], '--backup', str(self.backup))

    def test_explicit_adoption_preserves_full_bytes_and_backup(self):
        """DH04/08：具体预览绑定原件；回读外部备份后才追加规则。"""
        self.existing()
        self.run_cli('--agent', 'codex', ok=False)
        preview = self.run_cli('--agent', 'codex', '--adopt-agent')
        self.assertEqual(preview['files']['AGENTS.md'], 'update')
        self.assertEqual(preview['agent_adoptions']['AGENTS.md']['before_sha256'], hashlib.sha256(self.original).hexdigest())
        self.assertEqual((self.target / 'AGENTS.md').read_bytes(), self.original)
        result = self.adopted()
        self.assertEqual(result['backup'], str(self.backup))
        self.assertTrue((self.target / 'AGENTS.md').read_bytes().startswith(self.original))
        self.assertEqual((self.backup / 'original/AGENTS.md').read_bytes(), self.original)
        self.run_cli('--check')

    def test_updates_require_external_fresh_backup(self):
        """DH08：缺备份、内部备份与已有备份均整批阻断。"""
        self.existing()
        preview = self.run_cli('--agent', 'codex', '--adopt-agent')
        args = ['--agent', 'codex', '--adopt-agent', '--apply', '--approve', preview['fingerprint']]
        self.run_cli(*args, ok=False)
        self.run_cli(*args, '--backup', str(self.target / 'backup'), ok=False)
        self.backup.mkdir()
        self.run_cli(*args, '--backup', str(self.backup), ok=False)
        self.assertEqual(list(self.target.iterdir()), [self.target / 'AGENTS.md'])
        self.assertEqual((self.target / 'AGENTS.md').read_bytes(), self.original)

    def test_stale_adoption_fingerprint_blocks_all_writes(self):
        """DH08：预览后任意入口字节变化必须重新批准。"""
        self.existing()
        preview = self.run_cli('--agent', 'codex', '--adopt-agent')
        (self.target / 'AGENTS.md').write_bytes(self.original + b'new')
        self.run_cli('--agent', 'codex', '--adopt-agent', '--apply', '--approve', preview['fingerprint'], '--backup', str(self.backup), ok=False)
        self.assertFalse(self.backup.exists())
        self.assertFalse((self.target / 'docs').exists())

    def test_recovery_requires_same_preview_and_preserves_navigation(self):
        """DH08：恢复仅还原旧入口，保留本次新增文档目录。"""
        self.existing()
        self.adopted()
        preview = self.run_cli('--recover-agent', str(self.backup))
        self.run_cli('--recover-agent', str(self.backup), '--apply', '--approve', 'wrong', ok=False)
        self.run_cli('--recover-agent', str(self.backup), '--apply', '--approve', preview['fingerprint'])
        self.assertEqual((self.target / 'AGENTS.md').read_bytes(), self.original)
        self.assertTrue((self.target / 'docs/README.md').exists())

    def test_recovery_rejects_manual_entry_and_backup_tampering(self):
        """DH08：恢复不能覆盖人工增量或采用损坏备份。"""
        self.existing()
        self.adopted()
        entry = self.target / 'AGENTS.md'
        adopted = entry.read_bytes()
        entry.write_bytes(adopted + b'manual')
        self.run_cli('--recover-agent', str(self.backup), ok=False)
        entry.write_bytes(adopted)
        (self.backup / 'original/AGENTS.md').write_bytes(b'corrupt')
        self.run_cli('--recover-agent', str(self.backup), ok=False)

    def test_navigation_unique_appendix_preserved_without_validation_claim(self):
        """DH04：导航原文逐字相同时保留另一工具的唯一完整附加块。"""
        self.apply()
        paths = ['docs/README.md', 'docs/engineering/README.md']
        for name in paths:
            path = self.target / name
            path.write_text(path.read_text() + '\n' + BLOCK)
        before = {name: (self.target / name).read_bytes() for name in paths}
        result = self.run_cli('--check')
        self.assertEqual(sorted(result['external_blocks_unverified']), paths)
        self.apply()
        self.assertEqual(before, {name: (self.target / name).read_bytes() for name in paths})

    def test_navigation_manual_difference_still_blocks(self):
        """DH04：管理块不能遮蔽原导航正文或块外的人工差异。"""
        self.apply()
        path = self.target / 'docs/README.md'
        original = path.read_text()
        for text in [original.replace('项目文档总导航', '人工导航') + '\n' + BLOCK, original + '\n' + BLOCK + '人工尾文', BLOCK + original]:
            path.write_text(text)
            self.run_cli('--check', ok=False)

    def test_malicious_or_malformed_markers_block(self):
        """DH04：重复、倒序、缺失、内联和未知 baseline 标记均关闭通过路径。"""
        self.apply()
        path = self.target / 'docs/README.md'
        original = path.read_text()
        for block in [BLOCK + BLOCK, START, END + '\n' + START, 'prefix' + BLOCK, START + '\n' + START + '\n' + END, '<!-- aef:baseline:other -->\n' + BLOCK]:
            path.write_text(original + '\n' + block)
            self.run_cli('--check', ok=False)

    def test_adoption_rejects_broken_or_partial_routing_markers(self):
        """DH04：显式采用也不能把破损旧路由标记静默并为第二份规则。"""
        self.existing('规则\n<!-- aef-docs-routing:v1 -->\n残缺')
        self.run_cli('--agent', 'codex', '--adopt-agent', ok=False)
        self.assertFalse((self.target / 'docs').exists())

    def test_adopted_entry_old_rule_and_baseline_are_preserved(self):
        """DH04：Docs Init 先落地后，baseline 与人工内容可完整保留。"""
        self.apply()
        entry = self.target / 'AGENTS.md'
        text = '# 人工入口\n' + BLOCK + '\n' + entry.read_text()
        entry.write_text(text)
        self.run_cli('--check')
        self.apply('--adopt-agent')
        self.assertEqual(entry.read_text(), text)

    def test_navigation_block_drift_invalidates_old_plan(self):
        """DH08：虽然外部块不由本工具验证，其完整字节仍绑定预览。"""
        self.apply()
        path = self.target / 'docs/README.md'
        path.write_text(path.read_text() + '\n' + BLOCK)
        preview = self.run_cli()
        changed = path.read_text().replace('工程基线自有导航', '工程基线已更新导航')
        path.write_text(changed)
        self.run_cli('--apply', '--approve', preview['fingerprint'], ok=False)
        self.assertEqual(path.read_text(), changed)

    def test_malformed_recovery_record_is_structured_failure(self):
        """DH08：损坏备份字段不能导致未捕获异常或扩展恢复范围。"""
        self.existing()
        self.adopted()
        path = self.backup / 'record.json'
        original = json.loads(path.read_text())
        for entries in [{'docs/product/ideas.md': {}}, {'AGENTS.md': {}}, {'AGENTS.md': []}]:
            path.write_text(json.dumps({**original, 'entries': entries}))
            result = self.run_cli('--recover-agent', str(self.backup), ok=False)
            self.assertEqual(result['status'], 'blocked')

    def test_partial_entry_failure_returns_recovery_pointer(self):
        """DH08：第二个入口写入失败，首个入口仍可凭外部记录恢复。"""
        import sys
        from unittest.mock import patch
        sys.path.insert(0, str(test_docs.ROOT / 'scripts'))
        import agent_adoption
        import safe_files
        from layout import render
        self.existing()
        (self.target / 'CLAUDE.md').write_text('# 第二个旧入口\n')
        files, states, fingerprint = safe_files.plan(self.target, render('both'), True)
        original = agent_adoption.atomic
        def fail_second_entry(path, data, mode=0o644):
            """仅为目标第二入口注入磁盘异常，备份保持真实。"""
            if path == self.target / 'CLAUDE.md':
                raise OSError('合成磁盘失败')
            return original(path, data, mode)
        written = []
        with patch.object(agent_adoption, 'atomic', side_effect=fail_second_entry):
            with self.assertRaisesRegex(ValueError, '恢复.*' + str(self.backup)):
                safe_files.apply(self.target, files, states, written, str(self.backup), fingerprint)
        self.assertIn('AGENTS.md', written)
        preview = self.run_cli('--recover-agent', str(self.backup))
        self.run_cli('--recover-agent', str(self.backup), '--apply', '--approve', preview['fingerprint'])
        self.assertEqual((self.target / 'AGENTS.md').read_bytes(), self.original)

    def test_backup_readback_failure_never_updates_target(self):
        """DH08：实际备份文件损坏时必须在任何目标写入前阻断。"""
        import sys
        from unittest.mock import patch
        sys.path.insert(0, str(test_docs.ROOT / 'scripts'))
        import agent_adoption
        import safe_files
        from layout import render
        self.existing()
        files, states, fingerprint = safe_files.plan(self.target, render('codex'), True)
        original = agent_adoption.atomic
        def corrupt_backup(path, data, mode=0o644):
            """回读应识别原件备份的真实损坏。"""
            return original(path, b'corrupt' if path == self.backup / 'original/AGENTS.md' else data, mode)
        with patch.object(agent_adoption, 'atomic', side_effect=corrupt_backup):
            with self.assertRaisesRegex(ValueError, '回读'):
                safe_files.apply(self.target, files, states, [], str(self.backup), fingerprint)
        self.assertEqual(list(self.target.iterdir()), [self.target / 'AGENTS.md'])
        self.assertEqual((self.target / 'AGENTS.md').read_bytes(), self.original)

    def test_crlf_baseline_entry_preserves_exact_bytes(self):
        """DH04：旧入口的 CRLF 管理块也必须逐字节保留。"""
        self.existing(('# 旧入口\n\n' + BLOCK).replace('\n', '\r\n'))
        self.adopted()
        self.assertTrue((self.target / 'AGENTS.md').read_bytes().startswith(self.original))
        self.assertEqual((self.backup / 'original/AGENTS.md').read_bytes(), self.original)

    def test_hardlinked_old_entry_cannot_be_adopted(self):
        """DH08：旧入口有其他硬链接路径时不得采用或覆盖任何原件。"""
        import os
        self.existing()
        outside = self.base / 'other-entry.md'
        os.link(self.target / 'AGENTS.md', outside)
        result = self.run_cli('--agent', 'codex', '--adopt-agent', ok=False)
        self.assertIn('硬链接', result['error'])
        self.assertEqual(outside.read_bytes(), self.original)
        self.assertEqual((self.target / 'AGENTS.md').read_bytes(), self.original)
        self.assertFalse((self.target / 'docs').exists())
        self.assertFalse(self.backup.exists())

    def test_hardlinked_backup_original_cannot_be_recovered(self):
        """DH08：备份原件有其他硬链接时拒绝恢复，保留外部路径。"""
        import os
        self.existing()
        self.adopted()
        adopted = (self.target / 'AGENTS.md').read_bytes()
        outside = self.base / 'other-backup.md'
        os.link(self.backup / 'original/AGENTS.md', outside)
        result = self.run_cli('--recover-agent', str(self.backup), ok=False)
        self.assertIn('硬链接', result['error'])
        self.assertEqual(outside.read_bytes(), self.original)
        self.assertEqual((self.target / 'AGENTS.md').read_bytes(), adopted)

    def test_crlf_backup_restoration_preserves_exact_bytes(self):
        """DH08：采用再恢复后，CRLF 原入口必须逐字节相等。"""
        self.existing(('# 旧入口\n\n' + BLOCK + '\n尾文\n').replace('\n', '\r\n'))
        self.adopted()
        preview = self.run_cli('--recover-agent', str(self.backup))
        self.run_cli('--recover-agent', str(self.backup), '--apply', '--approve', preview['fingerprint'])
        self.assertEqual((self.target / 'AGENTS.md').read_bytes(), self.original)


if __name__ == '__main__':
    unittest.main(verbosity=2)
