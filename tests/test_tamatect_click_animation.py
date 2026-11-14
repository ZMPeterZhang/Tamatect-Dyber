import json
import os
import unittest

from DyberPet.conf import Act, basedir


class TamatectClickAnimationTests(unittest.TestCase):
    def test_idle_click_frame_is_excluded_from_default_animation(self):
        role_dir = os.path.join(basedir, 'res', 'role', 'Tamatect')
        with open(os.path.join(role_dir, 'pet_conf.json'), encoding='UTF-8') as file:
            pet_conf = json.load(file)
        with open(os.path.join(role_dir, 'act_conf.json'), encoding='UTF-8') as file:
            act_conf = json.load(file)

        pic_dict = {
            image_name: image_name
            for image_name in ('idle_0', 'idle_1', 'idle_2', 'idle_click_0')
        }
        idle = Act.init_act(act_conf['default'], pic_dict, 1, 'Tamatect')
        idle_click = Act.init_act(act_conf[pet_conf['patpat']], pic_dict, 1, 'Tamatect')

        self.assertEqual(idle.images, ['idle_0', 'idle_1', 'idle_2'])
        self.assertEqual(idle_click.images, ['idle_click_0'])


if __name__ == '__main__':
    unittest.main()
