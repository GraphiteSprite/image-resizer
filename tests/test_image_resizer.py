import os
import shutil
import unittest
from unittest.mock import patch, MagicMock, mock_open
from PIL import Image
from io import BytesIO
from image_resizer import resize_image, UndoManager, DragDropEntry


class TestResizeImage(unittest.TestCase):
    @patch("image_resizer.os.path.getsize")
    @patch("image_resizer.shutil.copy2")
    @patch("image_resizer.Image.open")
    def test_resize_image_skip_if_already_under_target(self, mock_open, mock_copy, mock_getsize):
        mock_getsize.return_value = 500 * 1024  # 500 KB (less than target 1 MB)
        input_path = "test.jpg"
        output_path = "output.jpg"
        
        result = resize_image(input_path, output_path, target_size_mb=1)
        
        mock_copy.assert_called_once_with(input_path, output_path)
        self.assertIsNone(result)

    @patch("image_resizer.os.path.getsize")
    @patch("image_resizer.Image.open")
    def test_resize_image_binary_search_to_target_size(self, mock_open, mock_getsize):
        mock_image = MagicMock()
        mock_image.size = (2000, 1000)
        mock_image.format = "JPEG"
        mock_open.return_value = mock_image
        mock_getsize.side_effect = [5 * 1024 * 1024, 1.5 * 1024 * 1024, 900 * 1024]  # Simulate decreasing size

        input_path = "test.jpg"
        output_path = "output.jpg"

        result = resize_image(input_path, output_path, target_size_mb=1)

        # Check that the image was resized multiple times to find optimal size
        self.assertIsNotNone(result)
        self.assertEqual(mock_image.resize.call_count, 3)

    @patch("image_resizer.os.path.getsize")
    @patch("image_resizer.Image.open")
    def test_resize_image_invalid_scaled_size(self, mock_open, mock_getsize):
        input_path = "test.jpg"
        output_path = "output.jpg"
        
        with self.assertRaises(ValueError):
            resize_image(input_path, output_path, scaled_size="invalid")

    @patch("image_resizer.Image.open")
    def test_resize_image_scaled_size_pixels(self, mock_open):
        mock_image = MagicMock()
        mock_image.size = (2000, 1000)
        mock_image.format = "PNG"
        mock_open.return_value = mock_image

        input_path = "test.png"
        output_path = "output.png"

        result = resize_image(input_path, output_path, scaled_size=500)

        self.assertIsNotNone(result)
        mock_image.resize.assert_called_once_with((1000, 500), Image.Resampling.LANCZOS)


class TestUndoManager(unittest.TestCase):
    def setUp(self):
        self.undo_manager = UndoManager()

    @patch("image_resizer.os.remove")
    def test_undo_last_batch_success(self, mock_remove):
        self.undo_manager.add_operation("input1.jpg", "output1.jpg")
        self.undo_manager.add_operation("input2.jpg", "output2.jpg")

        result = self.undo_manager.undo_last_batch()

        self.assertTrue(result)
        self.assertEqual(mock_remove.call_count, 2)

    @patch("image_resizer.os.remove")
    def test_undo_last_batch_with_missing_file(self, mock_remove):
        mock_remove.side_effect = [None, FileNotFoundError("File not found")]

        self.undo_manager.add_operation("input1.jpg", "output1.jpg")
        self.undo_manager.add_operation("input2.jpg", "output2.jpg")

        result = self.undo_manager.undo_last_batch()

        self.assertTrue(result)
        self.assertEqual(mock_remove.call_count, 2)

    def test_undo_no_operations(self):
        result = self.undo_manager.undo_last_batch()
        self.assertFalse(result)


class TestDragDropEntry(unittest.TestCase):
    def setUp(self):
        self.root = MagicMock()
        self.entry = DragDropEntry(master=self.root)

    def test_drop_valid_file(self):
        event = MagicMock()
        event.data = "{/path/to/file.jpg}"
        
        self.entry.drop(event)

        self.entry.delete.assert_called_once_with(0, "end")
        self.entry.insert.assert_called_once_with(0, "/path/to/file.jpg")

    def test_drop_invalid_file_format(self):
        event = MagicMock()
        event.data = "invalid_path"
        
        self.entry.drop(event)

        self.entry.delete.assert_called_once_with(0, "end")
        self.entry.insert.assert_called_once_with(0, "invalid_path")


if __name__ == "__main__":
    unittest.main()
