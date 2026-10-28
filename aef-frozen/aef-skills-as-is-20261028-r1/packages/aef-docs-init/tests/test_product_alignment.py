"""验证产品五类文档路由、旧名称退役及冲突保护。"""
import json
import unittest
import test_docs


class ProductAlignmentTests(unittest.TestCase):
    """只修改合成临时项目，复用实际 CLI。"""

    setUp = test_docs.DocsTests.setUp
    run_cli = test_docs.DocsTests.run_cli
    apply = test_docs.DocsTests.apply

    def test_five_document_routes(self):
        """ALIGN-03：五类产物均能取得精确路径。"""
        cases = [
            ('产品定义', None, 'docs/product/product-definition.md'),
            ('产品调研', 'users', 'docs/product/research/users.md'),
            ('用户故事', 'login', 'docs/product/requirements/login/story.md'),
            ('故事地图', None, 'docs/product/story-map.md'),
            ('迭代', 'v1', 'docs/project/sprints/v1.md'),
        ]
        for kind, name, expected in cases:
            with self.subTest(kind=kind):
                args = ['--route', kind, '--validate-path', expected]
                if name:
                    args += ['--name', name]
                self.assertEqual(self.run_cli(*args)['path'], expected)
        self.assertFalse(self.target.exists())

    def test_initialization_indexes_without_product_body(self):
        """ALIGN-03：初始化注册五类位置，但不虚构正文。"""
        self.apply()
        index = (self.target / 'docs/README.md').read_text()
        for kind in ('产品定义', '产品调研', '用户故事', '故事地图', '迭代'):
            self.assertIn('| ' + kind + ' |', index)
        for path in ('docs/product/product-definition.md', 'docs/product/story-map.md'):
            self.assertFalse((self.target / path).exists())
        self.run_cli('--check')

    def test_existing_definition_preserved(self):
        """ALIGN-04：查路由不覆盖旧正文，也不允许并行路径。"""
        self.apply()
        path = self.target / 'docs/product/product-definition.md'
        path.write_text('# 产品理念\n保留人工正文\n')
        before = path.read_bytes()
        self.run_cli('--route', '产品定义')
        self.run_cli('--route', '产品定义', '--validate-path', 'docs/product/positioning.md', ok=False)
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse((self.target / 'docs/product/positioning.md').exists())

    def test_retired_name_rejected(self):
        self.apply()
        before = {p: p.read_bytes() for p in self.target.rglob('*') if p.is_file()}
        self.run_cli('--route', '产品定位', ok=False)
        self.assertEqual(before, {p: p.read_bytes() for p in self.target.rglob('*') if p.is_file()})

    def test_old_contract_requires_review(self):
        """ALIGN-04：旧合同缺新增类型时只读阻断，不自动升级。"""
        self.apply()
        path = self.target / '.aef/docs-layout.json'
        data = json.loads(path.read_text())
        data['paths'].pop('产品定义', None)
        data['paths'].pop('故事地图', None)
        path.write_text(json.dumps(data, ensure_ascii=False))
        before = {p: p.read_bytes() for p in self.target.rglob('*') if p.is_file()}
        result = self.run_cli('--route', '产品定义', ok=False)
        self.assertIn('迁移', result['error'])
        self.assertEqual(before, {p: p.read_bytes() for p in self.target.rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main(verbosity=2)
