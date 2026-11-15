import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import DyberPet.settings as settings


class SettingsPersistenceTests(unittest.TestCase):
    def test_save_settings_creates_missing_data_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / 'data' / 'settings.json'

            with patch.object(settings, 'file_path', str(settings_path)):
                settings.save_settings()

            self.assertTrue(settings_path.is_file())


if __name__ == '__main__':
    unittest.main()
