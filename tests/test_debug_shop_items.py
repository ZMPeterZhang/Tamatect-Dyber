import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtGui import QImage

from DyberPet import debug_shop_items, settings


class FakeItemsData:
    def __init__(self):
        self.item_dict = {}
        self.reload_count = 0

    def init_data(self):
        self.reload_count += 1


class FakeSignal:
    def __init__(self):
        self.emit_count = 0

    def emit(self):
        self.emit_count += 1


class FakePet:
    curr_pet_name = 'Example'

    def __init__(self):
        self.item_layers = {}
        self.refresh_bag = FakeSignal()

    def _load_item_layers(self, pet_name):
        self.item_layers = {}
        if pet_name == 'Example':
            self.item_layers['lamp'] = {'config': {'inventory_item': 'Desk Lamp'}}

    def _load_legacy_accessory_layers(self):
        pass


class DebugShopItemTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.role_dir = self.root / 'res' / 'role' / 'Example'
        self.role_dir.mkdir(parents=True)
        self.source = self.root / 'source.png'
        image = QImage(2, 2, QImage.Format_ARGB32)
        image.fill(0xFFFFFFFF)
        self.assertTrue(image.save(str(self.source), 'PNG'))
        self.items_data = FakeItemsData()
        self.pet = FakePet()
        self.equipped_layers = {}
        self.patches = [
            patch.object(settings, 'BASEDIR', str(self.root)),
            patch.object(settings, 'items_data', self.items_data, create=True),
            patch.object(settings, 'equipped_item_layers', self.equipped_layers, create=True),
        ]
        for patcher in self.patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_placeable_item_creates_catalog_and_layer(self):
        debug_shop_items.register_shop_item(self.pet, 'Desk Lamp', 25, str(self.source))

        items_dir = self.role_dir / 'items'
        layers_dir = self.role_dir / 'layers'
        catalog = json.loads((items_dir / 'items_config.json').read_text(encoding='utf-8'))
        self.assertEqual(catalog['Desk Lamp']['type'], 'collection')
        self.assertEqual(catalog['Desk Lamp']['cost'], 25)
        self.assertTrue((layers_dir / 'desk_lamp.png').is_file())
        self.assertEqual(
            json.loads((layers_dir / 'desk_lamp.json').read_text(encoding='utf-8'))['inventory_item'],
            'Desk Lamp',
        )
        self.assertIn('Desk Lamp', self.equipped_layers)
        self.assertEqual(self.items_data.reload_count, 1)
        self.assertEqual(self.pet.refresh_bag.emit_count, 1)

    def test_health_consumable_does_not_create_a_layer(self):
        debug_shop_items.register_shop_item(self.pet, 'Health Drink', 10, str(self.source), health=12)

        items_dir = self.role_dir / 'items'
        catalog = json.loads((items_dir / 'items_config.json').read_text(encoding='utf-8'))
        self.assertEqual(catalog['Health Drink']['type'], 'consumable')
        self.assertEqual(catalog['Health Drink']['effect_HP'], 12)
        self.assertFalse((self.role_dir / 'layers').exists())

    def test_rejects_duplicate_names_case_insensitively(self):
        self.items_data.item_dict['desk lamp'] = {}

        with self.assertRaises(ValueError):
            debug_shop_items.register_shop_item(self.pet, 'Desk Lamp', 25, str(self.source))


if __name__ == '__main__':
    unittest.main()
