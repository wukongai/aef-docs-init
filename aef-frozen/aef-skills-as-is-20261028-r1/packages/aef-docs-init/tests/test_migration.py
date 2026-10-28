"""MIG-01 至 MIG-06：只使用合成项目验证迁移与恢复。"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'scripts/docs_migrate.py'


class MigrationTests(unittest.TestCase):
    """通过独立进程核验可交付的实际命令。"""

    def setUp(self):
        """准备脱敏 fixture 和范围外的决策文件。"""
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()
        self.target = self.base / 'project'
        self.target.mkdir()
        self.backup = self.base / 'backup'
        self.decisions = self.base / 'decisions.json'
        self.write('docs/adr/one.md', '# 决策\n\n保留原始结论。\n')
        self.write('docs/logs/day.md', '[决策](../adr/one.md#决定)\n')
        self.write('AGENTS.md', '# 原规则\n读取 `docs/adr/`。\n')
        self.write('.aef/lifecycle/1/manifest.json', json.dumps({'status':'charter','decision':'pending','evidence_path':'docs/adr/one.md'}))
        self.mapping = {'docs/adr/one.md': {'action':'move','to':'docs/engineering/adr/one.md','reason':'正文是已确认架构决策'},
                        'docs/logs/day.md': {'action':'move','to':'docs/project/logs/daily/day.md','reason':'正文是执行日报'}}
        self.save()

    def write(self, path, text):
        """写入当前测试目录。"""
        target = self.target / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')

    def save(self):
        """保存显式分类依据与目录引用映射。"""
        self.decisions.write_text(json.dumps({'files':self.mapping,'directories':{'docs/adr':'docs/engineering/adr','docs/logs':'docs/project/logs/daily'}}))

    def run_cli(self, *args, ok=True):
        """要求成功和拒绝均可机器读取。"""
        result = subprocess.run([sys.executable,'-B',str(CLI),'--target',str(self.target),*args],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        self.assertTrue(result.stdout, result.stderr)
        return json.loads(result.stdout)

    def preview(self, ok=True):
        """预览不会写入目标或备份。"""
        return self.run_cli('--decisions', str(self.decisions), ok=ok)

    def apply(self):
        """此授权仅限当前测试 fixture。"""
        preview = self.preview()
        return self.run_cli('--decisions',str(self.decisions),'--apply','--approve',preview['fingerprint'],'--backup',str(self.backup))

    def snapshot(self):
        """捕获所有文件字节用于保真比较。"""
        return {p.relative_to(self.target).as_posix():p.read_bytes() for p in self.target.rglob('*') if p.is_file()}

    def test_scan_preview_and_missing_approval(self):
        """MIG-01/02：默认扫描、歧义与未批准均不写入。"""
        before = self.snapshot()
        self.assertEqual(self.run_cli()['status'], 'scan')
        self.preview()
        self.run_cli('--decisions',str(self.decisions),'--apply','--backup',str(self.backup),ok=False)
        self.assertEqual(before,self.snapshot())
        self.assertFalse(self.backup.exists())
        self.write('docs/custom/mixed.md','业务与技术待讨论')
        self.assertIn('未分类', self.preview(ok=False)['error'])

    def test_migration_links_state_trace_and_idempotence(self):
        """MIG-03/04/05：逐文件追溯、链接修复、状态不变和幂等。"""
        before = self.snapshot()
        result = self.apply()
        self.assertEqual(result['status'],'applied')
        self.assertFalse((self.target/'docs/adr').exists())
        self.assertFalse((self.target/'docs/logs').exists())
        self.assertIn('../../../engineering/adr/one.md#决定',(self.target/'docs/project/logs/daily/day.md').read_text())
        state = json.loads((self.target/'.aef/lifecycle/1/manifest.json').read_text())
        self.assertEqual(state,{'status':'charter','decision':'pending','evidence_path':'docs/engineering/adr/one.md'})
        self.assertIn('docs/engineering/adr/',(self.target/'AGENTS.md').read_text())
        for path, data in before.items():
            self.assertEqual((self.backup/'original'/path).read_bytes(),data)
        self.run_cli('--verify',str(self.backup))
        after = self.snapshot()
        self.assertEqual(self.preview()['status'],'already_migrated')
        self.assertEqual(after,self.snapshot())

    def test_stale_plan(self):
        """MIG-02：批准后源内容变化则整批阻断。"""
        preview = self.preview()
        self.write('docs/adr/one.md','新的决策')
        self.run_cli('--decisions',str(self.decisions),'--apply','--approve',preview['fingerprint'],'--backup',str(self.backup),ok=False)
        self.assertFalse(self.backup.exists())

    def test_conflicts_and_identical_merge(self):
        """MIG-03：同名差异拒绝，明确相同归并保留来源。"""
        self.write('docs/engineering/adr/one.md','冲突')
        self.assertIn('冲突',self.preview(ok=False)['error'])
        self.write('docs/engineering/adr/one.md',(self.target/'docs/adr/one.md').read_text())
        self.apply()

    def test_navigation_retirement_requires_evidence(self):
        """MIG-03：旧导航需逐项审阅，绝不猜测可删除。"""
        self.write('docs/README.md','# 旧导航\n')
        self.mapping['docs/README.md']={'action':'retire','reason':'旧导航','redirect':'docs/README.md'}
        self.save()
        self.preview(ok=False)
        self.mapping['docs/README.md']['evidence']='已核验仅含旧目录导航，无业务正文'
        self.save()
        self.apply()
        self.assertEqual((self.backup/'original/docs/README.md').read_text(),'# 旧导航\n')

    def test_custom_classification_and_path_safety(self):
        """MIG-01/06：自定义资料须显式分类，越界/符号链接拒绝。"""
        self.write('docs/custom/research.md','用户访谈')
        self.mapping['docs/custom/research.md']={'action':'move','to':'docs/product/research/interviews.md','reason':'正文来自需求访谈'}
        self.save()
        self.preview()
        self.mapping['docs/custom/research.md']['to']='../escape'
        self.save()
        self.preview(ok=False)
        (self.target/'docs/linked').symlink_to(self.base)
        self.run_cli(ok=False)

    def test_recovery_and_drift_protection(self):
        """MIG-05：可完整恢复；用户后续编辑不能被回滚覆盖。"""
        before=self.snapshot()
        self.apply()
        preview=self.run_cli('--recover',str(self.backup))
        self.write('docs/engineering/adr/one.md','人工新改动')
        self.run_cli('--recover',str(self.backup),'--apply','--approve',preview['fingerprint'],ok=False)
        self.write('docs/engineering/adr/one.md',before['docs/adr/one.md'].decode())
        preview=self.run_cli('--recover',str(self.backup))
        self.run_cli('--recover',str(self.backup),'--apply','--approve',preview['fingerprint'])
        self.assertEqual(before,self.snapshot())

    def test_partial_failure_can_recover(self):
        """MIG-05：真实完成一次目标写入后注入 I/O 失败，仍能恢复。"""
        from unittest.mock import patch
        sys.path.insert(0, str(ROOT/'scripts'))
        import migration_plan
        import migration_store
        before=self.snapshot()
        plan=migration_plan.prepare(self.target,json.loads(self.decisions.read_text()))
        original=migration_store.atomic
        writes=[]
        def fail_second(path, data, mode=0o644):
            """只干扰目标写入，不干扰备份与恢复记录。"""
            if self.target in path.parents:
                writes.append(path)
                if len(writes)==2:
                    raise OSError('合成磁盘失败')
            return original(path,data,mode)
        with patch.object(migration_store,'atomic',side_effect=fail_second):
            with self.assertRaisesRegex(ValueError,'迁移未完成'):
                migration_store.execute(self.target,plan,self.backup,plan['report']['fingerprint'])
        self.assertNotEqual(before,self.snapshot())
        preview=self.run_cli('--recover',str(self.backup))
        self.run_cli('--recover',str(self.backup),'--apply','--approve',preview['fingerprint'])
        self.assertEqual(before,self.snapshot())

    def test_backup_corruption_and_nested_backup(self):
        """MIG-03/05：备份禁止放入目标，损坏原件时禁止恢复。"""
        preview=self.preview()
        self.run_cli('--decisions',str(self.decisions),'--apply','--approve',preview['fingerprint'],'--backup',str(self.target/'backup'),ok=False)
        self.apply()
        (self.backup/'original/docs/adr/one.md').write_text('损坏')
        self.run_cli('--recover',str(self.backup),ok=False)

    def test_reference_definitions_and_extra_config(self):
        """MIG-04：支持引用式链接和申报的路径配置，审批值不变。"""
        self.write('docs/logs/day.md','[决策][adr]\n\n[adr]: ../adr/one.md#决定\n')
        self.write('settings.json',json.dumps({'docs_path':'docs/adr','status':'approved','approval_ref':'human:42'}))
        preview=self.run_cli('--decisions',str(self.decisions),'--include','settings.json')
        self.run_cli('--decisions',str(self.decisions),'--include','settings.json','--apply','--approve',preview['fingerprint'],'--backup',str(self.backup))
        settings=json.loads((self.target/'settings.json').read_text())
        self.assertEqual(settings,{'docs_path':'docs/engineering/adr','status':'approved','approval_ref':'human:42'})
        self.assertIn('../../../engineering/adr/one.md#决定',(self.target/'docs/project/logs/daily/day.md').read_text())

    def test_unknown_machine_reference_blocks(self):
        """MIG-04：不支持的 JSON 字段不能带着旧路径假称成功。"""
        self.write('.aef/config.json',json.dumps({'unknown':'docs/adr/one.md'}))
        self.assertIn('残留旧路径',self.preview(ok=False)['error'])

    def test_directory_only_drift(self):
        """MIG-02：新增空目录也应使已批准预览失效。"""
        preview=self.preview()
        (self.target/'docs/extra-empty').mkdir()
        self.run_cli('--decisions',str(self.decisions),'--apply','--approve',preview['fingerprint'],'--backup',str(self.backup),ok=False)

    def test_fifo_rejected_without_blocking(self):
        """MIG-06：非常规文件及时拒绝，不读取管道。"""
        import os
        os.mkfifo(self.target/'docs/pipe.md')
        self.run_cli(ok=False)

    def test_preserve_rule_whitespace_and_ancestor_directories(self):
        """MIG-03/04：入口原文尾部及规则父目录也必须可还原。"""
        self.write('AGENTS.md','# 原规则\n\n  \n')
        self.write('.claude/rules/docs.md','遵循 `docs/adr/`。\n')
        before=self.snapshot()
        self.apply()
        self.assertTrue((self.target/'AGENTS.md').read_bytes().startswith(before['AGENTS.md']))
        preview=self.run_cli('--recover',str(self.backup))
        self.run_cli('--recover',str(self.backup),'--apply','--approve',preview['fingerprint'])
        self.assertEqual(before,self.snapshot())

    def test_file_directory_collision_blocks_in_preview(self):
        """MIG-02/06：文件与目录角色冲突须在备份前阻断。"""
        self.mapping['docs/adr/one.md']['to']='docs/engineering/adr/README.md/one.md'
        self.save()
        self.preview(ok=False)

    def test_credential_paths_and_completed_directory_drift(self):
        """MIG-02/06：凭证路径不读取；完成后空目录漂移不能冒充幂等。"""
        self.write('docs/.env','合成测试数据，无实际凭证')
        self.run_cli(ok=False)
        (self.target/'docs/.env').unlink()
        self.apply()
        (self.target/'docs/unreviewed').mkdir()
        self.preview(ok=False)

    def test_migrated_project_passes_original_check(self):
        """MIG-06：迁移结果仍满足首版目录与路由入口合同。"""
        self.apply()
        result=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/docs_init.py'),'--target',str(self.target),'--check'],capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
