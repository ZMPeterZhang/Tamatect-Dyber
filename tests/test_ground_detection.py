import unittest
from types import SimpleNamespace
from unittest import mock

from PySide6.QtCore import QPoint, QRect

from DyberPet import settings
from DyberPet.DyberPet import GROUND_DETECTION_OFFSET, PetWidget


class GroundDetectionTests(unittest.TestCase):
    def test_ground_detection_and_clamping_shift_down_15_pixels(self):
        widget = SimpleNamespace(
            current_screen=QRect(0, 0, 1000, 1000),
            screen_width=1000,
            screen_height=1000,
            floor_pos=0,
            current_anchor=[0, 0],
            pos=lambda: QPoint(450, 800),
            width=lambda: 100,
            height=lambda: 100,
            label=SimpleNamespace(width=lambda: 100, height=lambda: 100),
            move=mock.Mock(),
        )
        widget.limit_in_screen = lambda x, y: PetWidget.limit_in_screen(
            widget, x, y)

        PetWidget._update_floor_pos(widget)
        self.assertEqual(GROUND_DETECTION_OFFSET, 15)
        self.assertEqual(widget.floor_pos, 915)

        with mock.patch.object(settings, 'onfloor', 0):
            PetWidget._move_customized(widget, 0, 114)
            self.assertEqual(settings.onfloor, 0)
            self.assertEqual(widget.move.call_args.args, (450, 914))

            PetWidget._move_customized(widget, 0, 116)
            self.assertEqual(settings.onfloor, 1)
            self.assertEqual(widget.move.call_args.args, (450, 915))


if __name__ == '__main__':
    unittest.main()
