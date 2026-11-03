"""
Unit tests for core background cropping logic using standard library unittest.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
import numpy as np
from PIL import Image

from core.models import CropConfig
from core.cropper import find_content_bbox, crop_image, process_single_image
from core.batch import run_batch


def create_test_image(
    size=(200, 200),
    bg_color=(255, 255, 255),
    content_box=(50, 50, 150, 150),
    content_color=(40, 40, 40),
) -> Image.Image:
    """Helper to generate an image with a solid background and colored center block."""
    img = Image.new("RGB", size, bg_color)
    arr = np.array(img)
    x1, y1, x2, y2 = content_box
    arr[y1:y2, x1:x2] = content_color
    return Image.fromarray(arr)


class TestCropperCore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.tmp_path = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_find_content_bbox(self):
        img = create_test_image(
            size=(300, 300),
            bg_color=(250, 250, 250),
            content_box=(60, 80, 200, 220),
            content_color=(50, 50, 50),
        )
        config = CropConfig(threshold=225, padding=5, min_density=10)
        bbox = find_content_bbox(img, config)

        self.assertIsNotNone(bbox)
        self.assertEqual(bbox.left, 55)
        self.assertEqual(bbox.top, 75)
        self.assertEqual(bbox.right, 205)
        self.assertEqual(bbox.bottom, 225)

    def test_empty_image_fallback(self):
        img = Image.new("RGB", (200, 200), (255, 255, 255))
        config = CropConfig(threshold=225, padding=10, min_density=50)

        cropped, bbox, is_fallback = crop_image(img, config)
        self.assertTrue(is_fallback)
        self.assertIsNone(bbox)
        self.assertEqual(cropped.size, (200, 200))

    def test_process_single_image(self):
        img = create_test_image()
        input_file = self.tmp_path / "scan_sample.jpg"
        img.save(input_file, format="JPEG")

        out_folder = self.tmp_path / "cropped_output"
        config = CropConfig(threshold=225, padding=10, min_density=20)

        result = process_single_image(input_file, out_folder, config)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.output_path)
        self.assertTrue(result.output_path.exists())
        self.assertLess(result.cropped_size[0], result.original_size[0])
        self.assertLess(result.cropped_size[1], result.original_size[1])

    def test_run_batch(self):
        in_folder = self.tmp_path / "inputs"
        in_folder.mkdir()
        out_folder = self.tmp_path / "outputs"

        files = []
        for i in range(3):
            f = in_folder / f"test_{i}.png"
            img = create_test_image(content_box=(20 + i * 10, 20 + i * 10, 100, 100))
            img.save(f)
            files.append(f)

        progress_events = []

        def on_prog(idx, total, res):
            progress_events.append((idx, total, res.success))

        results = run_batch(files, out_folder, on_progress=on_prog)

        self.assertEqual(len(results), 3)
        self.assertEqual(len(progress_events), 3)
        self.assertTrue(all(r.success for r in results))


if __name__ == "__main__":
    unittest.main()
