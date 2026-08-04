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


if __name__ == "__main__":
    unittest.main()
