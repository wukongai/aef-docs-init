"""通过独立进程验证完整文档目录与持续落点能力。"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/docs_init.py"


class DocsTests(unittest.TestCase):
    """仅使用临时目标，不修改用户项目。"""

    def setUp(self):
        """准备真实路径，避开系统临时目录别名。"""
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()
        self.target = self.base / "project"

    def run_cli(self, *args, ok=True):
        """调用 CLI，要求失败也提供结构化解释。"""
        result = subprocess.run([sys.executable, "-B", str(CLI), "--target", str(self.target), *args], capture_output=True, text=True, timeout=4)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        self.assertTrue(result.stdout, result.stderr)
        return json.loads(result.stdout)

    def apply(self, *args):
        """只批准本测试 fixture 的刚生成预览。"""
        preview = self.run_cli(*args)
        return self.run_cli(*args, "--apply", "--approve", preview["fingerprint"])

    def test_dry_run_and_unapproved(self):
        """DOC-05：预览和未批准操作不创建目标。"""
        self.run_cli()
        self.run_cli("--apply", ok=False)
        self.assertFalse(self.target.exists())

    def test_full_static_tree(self):
        """DOC-01：完整静态分类与 README 全部存在。"""
        self.apply()
        expected = json.loads((ROOT / "tests/fixtures/directories.json").read_text())
        actual = sorted(p.relative_to(self.target).as_posix() for p in (self.target / "docs").rglob("*") if p.is_dir())
        self.assertEqual(actual, sorted(expected))
        for path in expected:
            self.assertTrue((self.target / path / "README.md").is_file(), path)
        self.assertFalse(any("<" in str(p) for p in self.target.rglob("*")))
        self.assertFalse((self.target / "docs/constitution.md").exists())

    def test_docs_only_and_idempotence(self):
        """DOC-02/05：无业务工程目录且重复执行不改变文件。"""
        self.apply()
        before = {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in self.target.rglob("*") if p.is_file()}
        self.apply()
        after = {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in self.target.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual({p.name for p in self.target.iterdir()}, {"docs", ".aef", "AGENTS.md", "CLAUDE.md"})
        self.run_cli("--check")

    def test_route_without_initialization(self):
        """DOC-03：查询可先于初始化，且无副作用。"""
        routes = json.loads((ROOT / "tests/fixtures/routes.json").read_text())
        for kind, expected in routes.items():
            args = ["--route", kind]
            if "0.1.0" in expected:
                args += ["--name", "0.1.0"]
            if kind in ("拟议规格", "生效规格"):
                args += ["--name", "search"]
            self.assertEqual(self.run_cli(*args)["path"], expected)
        self.assertFalse(self.target.exists())

    def test_routing_validation(self):
        """DOC-03：动态实例与错误路径明确阻断。"""
        self.run_cli("--route", "拟议规格", ok=False)
        self.run_cli("--route", "拟议规格", "--name", "../escape", ok=False)
        self.run_cli("--route", "不存在", ok=False)
        self.run_cli("--route", "日报", "--name", "2026-10-08", "--validate-path", "docs/project/logs/daily/2026-10-08.md")
        self.run_cli("--route", "日报", "--name", "2026-10-08", "--validate-path", "docs/knowledge/team/learning/2026-10-08.md", ok=False)
        self.assertFalse(self.target.exists())

    def test_persistent_rules_and_config(self):
        """DOC-04：入口可达索引，源合同与项目配置一致。"""
        self.apply()
        source = json.loads((ROOT / "templates/directory-contract.json").read_text())
        project = json.loads((self.target / ".aef/docs-layout.json").read_text())
        self.assertEqual(project["paths"], source["paths"])
        for entry in ["AGENTS.md", "CLAUDE.md"]:
            text = (self.target / entry).read_text()
            self.assertIn("docs/README.md", text)
            self.assertIn(".aef/docs-layout.json", text)
        index = (self.target / "docs/README.md").read_text()
        for path in source["paths"].values():
            self.assertIn(path, index)
        (self.target / "docs/README.md").write_text("人工编辑")
        self.run_cli("--check", ok=False)

    def test_conflict_and_existing_project(self):
        """DOC-05/06：旧入口冲突整批阻断，none 明确未接入。"""
        self.target.mkdir()
        (self.target / "AGENTS.md").write_text("已有规则")
        self.run_cli(ok=False)
        self.assertEqual(list(self.target.iterdir()), [self.target / "AGENTS.md"])
        result = self.apply("--agent", "none")
        self.assertEqual(result["agent_projection"], "none")
        self.assertEqual((self.target / "AGENTS.md").read_text(), "已有规则")
        self.assertFalse((self.target / ".aef/profile.json").exists())
        self.assertFalse((self.target / ".aef/lifecycle").exists())

    def test_paths_and_stale_plan(self):
        """DOC-05：穿越、链接及陈旧计划阻断。"""
        original = self.target
        self.target = self.base / ".." / "escape"
        self.run_cli(ok=False)
        self.target = original
        preview = self.run_cli()
        self.target.mkdir()
        outside = self.base / "outside"
        outside.mkdir()
        (self.target / "docs").symlink_to(outside, target_is_directory=True)
        self.run_cli("--apply", "--approve", preview["fingerprint"], ok=False)
        self.assertEqual(list(outside.iterdir()), [])

    def test_no_private_content(self):
        """DOC-06：生成内容无私有路径、旧品牌或工程脚手架。"""
        self.apply()
        text = "\n".join(p.read_text() for p in self.target.rglob("*") if p.is_file())
        for marker in ["/Users/", "ai-native-kit", "docs/superpowers", "BEGIN " + "PRIVATE KEY"]:
            self.assertNotIn(marker, text)

    def test_nonregular_config(self):
        """DOC-05：机器配置为管道时及时拒绝，不阻塞。"""
        import os
        (self.target / ".aef").mkdir(parents=True)
        os.mkfifo(self.target / ".aef/docs-layout.json")
        self.run_cli(ok=False)
        self.assertFalse((self.target / "docs").exists())

    def test_contract_drift(self):
        """DOC-03：已存合同被修改时查询也停止。"""
        self.apply()
        path = self.target / ".aef/docs-layout.json"
        data = json.loads(path.read_text())
        data["paths"]["日报"] = "docs/knowledge/team/learning/"
        path.write_text(json.dumps(data))
        self.run_cli("--route", "日报", ok=False)

    def test_portable_copy(self):
        """DOC-06：只复制独立包，在其他工作目录可运行。"""
        import shutil
        package = self.base / "portable"
        shutil.copytree(ROOT, package)
        result = subprocess.run([sys.executable, "-B", str(package / "scripts/docs_init.py"), "--target", str(self.target)], cwd=self.base, capture_output=True, text=True, timeout=4)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "preview")
        self.assertFalse(self.target.exists())

    def test_existing_rule_extension(self):
        """DOC-04/05：已有相同规则外的用户内容原样保留。"""
        self.apply()
        path = self.target / "AGENTS.md"
        content = "# 用户原有规则\n\n" + path.read_text() + "\n其他用户规则\n"
        path.write_text(content)
        self.run_cli("--check")
        self.assertEqual(path.read_text(), content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
