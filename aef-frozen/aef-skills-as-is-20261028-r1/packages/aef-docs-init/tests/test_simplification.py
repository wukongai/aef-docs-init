"""通过真实 CLI 验证轻量分类、兼容阻断与领域保真。"""
import json
import unittest
import test_docs

ROOT = test_docs.ROOT


class SimplificationTests(unittest.TestCase):
    """复用临时项目与 CLI 驱动，所有写入限于 fixture。"""

    setUp = test_docs.DocsTests.setUp
    run_cli = test_docs.DocsTests.run_cli
    apply = test_docs.DocsTests.apply

    def test_product_routes(self):
        """SIM-01：点子、故事合并及 JSON 兼容均有明确落点。"""
        self.assertEqual(self.run_cli('--route', '点子')['path'], 'docs/product/ideas.md')
        for kind in ('需求发现', '用户故事'):
            self.assertEqual(self.run_cli('--route', kind, '--name', 'login')['path'], 'docs/product/requirements/login/story.md')
        self.assertEqual(self.run_cli('--route', '故事卡', '--name', 'login')['path'], 'docs/product/requirements/login/story-card.json')
        self.assertFalse(self.target.exists())

    def test_board_and_logs(self):
        """SIM-02：具名待办复用任务，日报周报不冲突。"""
        for kind in ('看板', '待办'):
            self.assertEqual(self.run_cli('--route', kind)['path'], 'docs/project/board.md')
        self.assertEqual(self.run_cli('--route', '待办', '--name', 'login')['path'], self.run_cli('--route', '任务', '--name', 'login')['path'])
        for kind, suffix in (('日报', 'daily'), ('周报', 'weekly')):
            for name in ('2026-10-09', '2026-10-09.md', '2026-10-09-' + suffix + '.md'):
                self.assertEqual(self.run_cli('--route', kind, '--name', name)['path'], 'docs/project/logs/2026-10-09-' + suffix + '.md')
        self.run_cli('--route', '日报', '--name', 'day.json', ok=False)
        self.run_cli('--route', '待办', '--name', '../escape', ok=False)

    def test_old_contract_is_not_silently_upgraded(self):
        """SIM-03：旧合同留在原位，拒绝用新路径继续写入。"""
        self.apply()
        path = self.target / '.aef/docs-layout.json'
        data = json.loads(path.read_text())
        data['paths']['用户故事'] = 'docs/product/requirements/<需求名>/user-story.md'
        path.write_text(json.dumps(data))
        before = {str(p): p.read_bytes() for p in self.target.rglob('*') if p.is_file()}
        result = self.run_cli('--route', '用户故事', '--name', 'login', ok=False)
        self.assertIn('迁移', result['error'])
        self.run_cli(ok=False)
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.target.rglob('*') if p.is_file()})

    def test_six_domains_and_preserved_routes(self):
        """SIM-03：六领域不变，四个未调整领域与基线完全一致。"""
        self.apply()
        self.assertEqual({p.name for p in (self.target / 'docs').iterdir() if p.is_dir()}, {'product', 'project', 'engineering', 'business', 'customer-success', 'knowledge'})
        baseline = json.loads((ROOT / 'tests/fixtures/preserved-routes.json').read_text())
        current = json.loads((ROOT / 'templates/directory-contract.json').read_text())['paths']
        self.assertEqual({k: v for k, v in current.items() if any(v.startswith('docs/' + d + '/') for d in ('engineering', 'business', 'customer-success', 'knowledge'))}, baseline)
        for path in ('docs/project/backlog', 'docs/project/logs/daily', 'docs/project/logs/weekly'):
            self.assertFalse((self.target / path).exists())
        self.assertFalse((self.target / 'docs/product/ideas.md').exists())
        self.assertFalse((self.target / 'docs/project/board.md').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
