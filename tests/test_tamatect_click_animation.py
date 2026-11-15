import json
import os
from types import SimpleNamespace
import unittest
from unittest import mock

from PySide6.QtGui import QColor, QImage

from DyberPet import settings
from DyberPet.conf import Act, CheckCharFiles, basedir
from DyberPet.modules import Interaction_worker


class TamatectClickAnimationTests(unittest.TestCase):
    def test_idle_click_frame_is_excluded_from_default_animation(self):
        role_dir = os.path.join(basedir, 'res', 'role', 'Tamatect')
        with open(os.path.join(role_dir, 'pet_conf.json'), encoding='UTF-8') as file:
            pet_conf = json.load(file)
        with open(os.path.join(role_dir, 'act_conf.json'), encoding='UTF-8') as file:
            act_conf = json.load(file)

        action_dir = os.path.join(role_dir, 'action')
        pic_dict = {
            os.path.splitext(file_name)[0]: os.path.splitext(file_name)[0]
            for file_name in os.listdir(action_dir)
            if file_name.endswith('.png')
        }
        idle = Act.init_act(act_conf['default'], pic_dict, 1, 'Tamatect')
        idle_click = Act.init_act(act_conf[pet_conf['patpat']], pic_dict, 1, 'Tamatect')

        self.assertEqual(idle.images, ['idle_0', 'idle_1', 'idle_2'])
        self.assertEqual(idle_click.images, ['idle_click_0'])

    def test_drag_fall_and_landing_actions_load_named_frames(self):
        role_dir = os.path.join(basedir, 'res', 'role', 'Tamatect')
        with open(os.path.join(role_dir, 'pet_conf.json'), encoding='UTF-8') as file:
            pet_conf = json.load(file)
        with open(os.path.join(role_dir, 'act_conf.json'), encoding='UTF-8') as file:
            act_conf = json.load(file)

        action_dir = os.path.join(role_dir, 'action')
        pic_dict = {
            os.path.splitext(file_name)[0]: os.path.splitext(file_name)[0]
            for file_name in os.listdir(action_dir)
            if file_name.endswith('.png')
        }

        self.assertEqual(
            Act.init_act(act_conf['drag'], pic_dict, 1, 'Tamatect').images,
            ['drag_000'],
        )
        self.assertEqual(
            Act.init_act(act_conf['fall'], pic_dict, 1, 'Tamatect').images,
            ['falling_000'],
        )
        self.assertEqual(pet_conf['on_floor'], 'land')
        self.assertEqual(
            Act.init_act(act_conf['land'], pic_dict, 1, 'Tamatect').images,
            ['land_000', 'land_001'],
        )
        self.assertEqual(CheckCharFiles(role_dir), (0, None))

    def test_replacement_frames_use_native_size_at_role_scale_one(self):
        role_dir = os.path.join(basedir, 'res', 'role', 'Tamatect')
        with open(os.path.join(role_dir, 'pet_conf.json'), encoding='UTF-8') as file:
            pet_conf = json.load(file)
        with open(os.path.join(role_dir, 'act_conf.json'), encoding='UTF-8') as file:
            act_conf = json.load(file)
        with open(os.path.join(role_dir, 'event_conf.json'), encoding='UTF-8') as file:
            event_conf = json.load(file)

        self.assertEqual(pet_conf['scale'], 1.0)
        self.assertEqual((pet_conf['width'], pet_conf['height']), (300, 300))

        action_dir = os.path.join(role_dir, 'action')
        pic_dict = {
            os.path.splitext(file_name)[0]:
            QImage(os.path.join(action_dir, file_name))
            for file_name in os.listdir(action_dir)
            if file_name.endswith('.png')
        }
        pic_names = {name: name for name in pic_dict}

        for action_name in (
                'default', 'idle_click', 'focus', 'feed_2', 'sleep',
                'drag', 'fall', 'land'):
            with self.subTest(action=action_name):
                action = Act.init_act(
                    act_conf[action_name], pic_dict, 1.0, 'Tamatect')
                for frame in action.images:
                    self.assertEqual(
                        (frame.width(), frame.height()), (300, 300))

        self.assertEqual(pet_conf['focus'], 'focus')
        self.assertEqual(pet_conf['feed_action'], 'Eating')
        feed_group = next(
            action for action in pet_conf['random_act']
            if action['name'] == pet_conf['feed_action'])
        self.assertEqual(feed_group['act_list'], ['feed_2'])
        self.assertEqual(
            pet_conf['aec_actions'],
            {'work': 'focus', 'sleep': 'sleep'},
        )
        self.assertEqual(
            Act.init_act(act_conf['focus'], pic_names, 1.0, 'Tamatect').images,
            ['focus_1', 'focus_2', 'focus_3', 'focus_4'],
        )
        self.assertEqual(
            Act.init_act(act_conf['feed_2'], pic_names, 1.0, 'Tamatect').images,
            [
                'eating_ordinary_1', 'eating_ordinary_2',
                'eating_ordinary_3', 'eating_ordinary_4',
            ],
        )
        self.assertEqual(
            Act.init_act(act_conf['sleep'], pic_names, 1.0, 'Tamatect').images,
            ['sleeping_0'],
        )
        self.assertEqual(event_conf['events'][0]['animation'], 'Idle')
        for action_name in ('feed_1', 'feed_3', 'work', 'bim_crash'):
            self.assertNotIn(action_name, act_conf)
        self.assertIn('aec_hard_hat', act_conf)

    def test_food_use_uses_configured_feed_animation(self):
        worker = SimpleNamespace(
            pet_conf=SimpleNamespace(
                feed_action='Eating',
                act_name=['Eating'],
            ),
            start_interact=mock.Mock(),
        )

        Interaction_worker.use_item(worker, 'coffee')

        worker.start_interact.assert_called_once_with('animat', 'Eating')

    def test_food_use_falls_back_to_default_animation(self):
        worker = SimpleNamespace(start_interact=mock.Mock())

        Interaction_worker.use_item(worker, 'coffee')

        worker.start_interact.assert_called_once_with('animat', 'default')

    def test_landing_interaction_dispatches_and_plays_both_frames_once(self):
        worker = SimpleNamespace(
            pet_conf=SimpleNamespace(
                on_floor=Act(
                    images=['land_000', 'land_001'],
                    act_num=1,
                    frame_refresh=0.5,
                    anchor=[0, 0],
                ),
                interact_speed=20,
            ),
            sig_setimg_inter=mock.Mock(),
        )
        frames = []
        stop_frames = []

        def display_next_frame(act):
            if settings.current_act != act:
                settings.current_act = act
                settings.playid = 0
            frame_index = settings.playid
            frames.append(act.images[frame_index // 25])
            settings.previous_img = settings.current_img
            settings.current_img = frames[-1]
            settings.previous_anchor = settings.current_anchor
            settings.current_anchor = [0, 0]
            settings.playid = (frame_index + 1) % 50

        worker.img_from_act = display_next_frame
        worker.stop_interact = mock.Mock(
            side_effect=lambda: stop_frames.append(len(frames)))
        worker.start_interact = mock.Mock()
        with mock.patch.multiple(
            settings,
            set_fall=1,
            onfloor=1,
            fall_right=False,
            tunable_scale=1,
            playid=49,
            current_act='fall',
            current_img='before',
            previous_img='before',
            current_anchor=[0, 0],
            previous_anchor=[0, 0],
            create=True,
        ):
            Interaction_worker.mousedrag(worker, None)
            worker.start_interact.assert_called_once_with('onfloor')

            for _ in range(50):
                Interaction_worker.onfloor(worker)

        self.assertEqual(frames, ['land_000'] * 25 + ['land_001'] * 25)
        self.assertEqual(stop_frames, [50])

    def test_landing_tracks_mirroring_for_equipped_layers(self):
        image = QImage(2, 1, QImage.Format_RGB32)
        image.setPixelColor(0, 0, QColor('red'))
        image.setPixelColor(1, 0, QColor('blue'))
        landing = Act(images=[image], act_num=1, frame_refresh=0.5, anchor=[2, 3])
        worker = SimpleNamespace(
            pet_conf=SimpleNamespace(on_floor=landing, interact_speed=20),
            sig_setimg_inter=mock.Mock(),
            stop_interact=mock.Mock(),
        )
        worker.img_from_act = lambda act: Interaction_worker.img_from_act(worker, act)
        with mock.patch.multiple(
            settings,
            fall_right=True,
            tunable_scale=1,
            current_act=None,
            playid=0,
            current_img=QImage(),
            previous_img=QImage(),
            current_anchor=[0, 0],
            previous_anchor=[0, 0],
            current_img_mirrored=False,
            create=True,
        ):
            Interaction_worker.onfloor(worker)
            self.assertTrue(settings.current_img_mirrored)
            self.assertEqual(settings.current_img.pixelColor(0, 0), QColor('blue'))

            settings.fall_right = False
            Interaction_worker.onfloor(worker)
            self.assertFalse(settings.current_img_mirrored)
            self.assertEqual(settings.current_img.pixelColor(0, 0), QColor('red'))


if __name__ == '__main__':
    unittest.main()
