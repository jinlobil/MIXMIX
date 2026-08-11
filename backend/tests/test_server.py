import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.storage = Path(self.temp.name)
        self.patches = [
            patch.object(server, "STORAGE", self.storage),
            patch.object(server, "IMAGE_DIR", self.storage / "images"),
            patch.object(server, "PROMPTS_FILE", self.storage / "prompts.json"),
            patch.object(server, "CATEGORIES_FILE", self.storage / "categories.json"),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def prompt(self, images=None):
        return {"id":"one", "category":"face", "title":"테스트", "prompt":"soft light", "images":images or []}

    def test_writes_metadata_to_json(self):
        saved = server.save_prompts([self.prompt()])
        self.assertEqual(saved, server.load_prompts())
        self.assertTrue(server.PROMPTS_FILE.is_file())

    def test_extracts_data_url_to_separate_image_file(self):
        data = base64.b64encode(b"fake-png-content").decode()
        saved = server.save_prompts([self.prompt([f"data:image/png;base64,{data}"])])
        self.assertRegex(saved[0]["images"][0], r"^/uploads/[a-f0-9]{32}\.png$")
        self.assertEqual(len(list(server.IMAGE_DIR.iterdir())), 1)
        self.assertNotIn("base64", server.PROMPTS_FILE.read_text())

    def test_removes_orphaned_image_when_prompt_is_deleted(self):
        data = base64.b64encode(b"fake-image").decode()
        server.save_prompts([self.prompt([f"data:image/jpeg;base64,{data}"])])
        image = next(server.IMAGE_DIR.iterdir())
        server.save_prompts([])
        self.assertFalse(image.exists())

    def test_rejects_more_than_three_images(self):
        with self.assertRaisesRegex(ValueError, "up to 3"):
            server.save_prompts([self.prompt(["x"] * 4)])

    def test_categories_are_saved_to_separate_json(self):
        categories = [["custom", "커스텀", "◇"]]
        self.assertEqual(server.save_categories(categories), categories)
        self.assertEqual(server.load_categories(), categories)
        self.assertTrue(server.CATEGORIES_FILE.is_file())

    def test_category_in_use_cannot_be_removed_before_prompts(self):
        server.save_prompts([self.prompt()])
        with self.assertRaisesRegex(ValueError, "still has prompts"):
            server.save_categories([["hair", "헤어", "⌇"]])


class WindowsBatchTests(unittest.TestCase):
    def test_installer_checks_versions_and_uses_winget(self):
        root = Path(__file__).resolve().parents[2]
        content = (root / "install.bat").read_text(encoding="utf-8")
        self.assertIn("scripts\\check-python.py", content)
        self.assertIn("scripts\\check-node.js", content)
        self.assertIn("Python.Python.3.12", content)
        self.assertIn("OpenJS.NodeJS.LTS", content)
        self.assertIn("where winget", content)

    def test_start_batch_validates_environment_and_runs_app(self):
        root = Path(__file__).resolve().parents[2]
        content = (root / "start.bat").read_text(encoding="utf-8")
        self.assertIn("scripts\\check-python.py", content)
        self.assertIn("scripts\\check-node.js", content)
        self.assertIn("npm start", content)
        self.assertIn("http://127.0.0.1:4173", content)


class FrontendFormattingTests(unittest.TestCase):
    def test_combined_prompt_has_category_headers_and_blank_lines(self):
        root = Path(__file__).resolve().parents[2]
        app = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        styles = (root / "frontend" / "styles.css").read_text(encoding="utf-8")
        self.assertIn("`[${name}]\\n${item.prompt}`", app)
        self.assertIn(".filter(Boolean).join('\\n\\n')", app)
        self.assertIn("const text=buildCombinedPrompt()", app)
        self.assertIn("white-space:pre-wrap", styles)

    def test_prompt_editor_supports_metadata_and_image_changes(self):
        root = Path(__file__).resolve().parents[2]
        app = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
        self.assertIn("data-edit", app)
        self.assertIn("editingId=prompt?.id||null", app)
        self.assertIn("data-remove-image", app)
        self.assertIn("prompts.map(prompt=>prompt.id===editingId?item:prompt)", app)
        self.assertIn('id="savePromptButton"', html)

    def test_prompt_cards_prioritize_taller_images_and_hide_prompt_excerpt(self):
        root = Path(__file__).resolve().parents[2]
        app = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        styles = (root / "frontend" / "styles.css").read_text(encoding="utf-8")
        self.assertNotIn('<p>${escapeHtml(p.prompt)}</p>', app)
        self.assertIn("aspect-ratio:3/4", styles)
        self.assertIn("object-position:center top", styles)

    def test_category_manager_supports_add_rename_and_delete(self):
        root = Path(__file__).resolve().parents[2]
        app = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
        self.assertIn("persistCategories", app)
        self.assertIn("addCategoryButton", app)
        self.assertIn("data-delete-category", app)
        self.assertIn('id="categoryDialog"', html)
        self.assertIn('id="manageCategoriesButton"', html)
        self.assertIn('draggable="true"', app)
        self.assertIn("dragstart", app)
        self.assertIn("dragover", app)
        self.assertIn("categoryValuesFromEditor", app)

    def test_prompt_input_allows_5000_characters_and_assets_are_not_cached(self):
        root = Path(__file__).resolve().parents[2]
        html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
        server_source = (root / "frontend" / "server.js").read_text(encoding="utf-8")
        self.assertIn('maxlength="5000"', html)
        self.assertIn('id="promptLength"', html)
        self.assertIn('Cache-Control', server_source)
        self.assertIn('no-store', server_source)


if __name__ == "__main__":
    unittest.main()
