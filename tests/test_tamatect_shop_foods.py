import json
import os
import unittest

from DyberPet.conf import basedir, checkItemMOD


class TamatectShopFoodTests(unittest.TestCase):
    def test_new_foods_are_purchasable_tamatect_consumables(self):
        item_dir = os.path.join(basedir, 'res', 'items', 'Default')
        with open(
                os.path.join(item_dir, 'items_config.json'),
                encoding='UTF-8') as item_file:
            items = json.load(item_file)

        for name in ('Coffee', 'Coke', 'Onigiri', 'Pizza'):
            with self.subTest(item=name):
                item = items[name]
                self.assertGreater(item['cost'], 0)
                self.assertEqual(item['drop_rate'], 0)
                self.assertEqual(item['pet_limit'], ['Tamatect'])
                self.assertGreater(item['effect_HP'], 0)
                self.assertTrue(os.path.isfile(
                    os.path.join(item_dir, item['image'])))

        self.assertEqual(checkItemMOD(item_dir), (0, None))


if __name__ == '__main__':
    unittest.main()
