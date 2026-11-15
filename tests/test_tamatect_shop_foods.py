import json
import os
import unittest
from unittest.mock import patch

from DyberPet import conf
from DyberPet.conf import basedir, checkItemMOD


class TamatectShopFoodTests(unittest.TestCase):
    def test_new_foods_are_purchasable_tamatect_consumables(self):
        item_dir = os.path.join(basedir, 'res', 'items', 'Default')
        with open(
                os.path.join(item_dir, 'items_config.json'),
                encoding='UTF-8') as item_file:
            items = json.load(item_file)

        for name in ('Coffee', 'Coke', 'Energy Drink', 'Onigiri', 'Pizza', 'Gyudon'):
            with self.subTest(item=name):
                item = items[name]
                self.assertGreater(item['cost'], 0)
                self.assertEqual(item['drop_rate'], 0)
                self.assertEqual(item['pet_limit'], ['Tamatect'])
                self.assertGreater(item['effect_HP'], 0)
                self.assertTrue(os.path.isfile(
                    os.path.join(item_dir, item['image'])))

        self.assertEqual(checkItemMOD(item_dir), (0, None))

    def test_legacy_item_id_uses_english_display_name(self):
        item_data = conf.ItemData.__new__(conf.ItemData)
        item_data.HUNGERSTR = 'Satiety'
        item_data.FAVORSTR = 'Favorability'
        item_data.reward_dict = {}
        config = {
            'display_name': 'Hamburger',
            'image': 'hamburger.png',
            'effect_HP': 1,
            'description': 'A tasty hamburger.',
        }

        with patch.object(conf, '_load_item_img', return_value=object()):
            item = item_data.init_item(config, '汉堡', '', 'Default')

        self.assertEqual(item['name'], '汉堡')
        self.assertEqual(item['display_name'], 'Hamburger')
        self.assertIn('Hamburger', item['hint'])
        item_data.item_dict = {'汉堡': item}
        self.assertEqual(item_data.get_display_name('汉堡'), 'Hamburger')
        self.assertEqual(item_data.get_display_name('legacy item'), 'legacy item')


if __name__ == '__main__':
    unittest.main()
