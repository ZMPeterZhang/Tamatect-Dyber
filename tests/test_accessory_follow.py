import unittest
from unittest import mock

from DyberPet import settings
from DyberPet.Accessory import QAccessory


class FakePoint:
    def __init__(self, x, y):
        self._x = x
        self._y = y

    def x(self):
        return self._x

    def y(self):
        return self._y


class FakeAccessory:
    def __init__(self):
        self.follow_main = True
        self.main_falling = False
        self.recovering_from_fall = False
        self.current_anchor = [10, 20]
        self.destination = [110, 120]
        self.at_destination = False
        self.move_right = False
        self.delay_respond = 167
        self.delay_timer = 0
        self.speed_follow_main = 5
        self.position = [60, 70]

    def pos(self):
        return FakePoint(*self.position)

    def move(self, x, y):
        self.position = [x, y]

    def _raise_if_above_main(self):
        pass

    @staticmethod
    def _main_is_falling():
        return bool(settings.set_fall) and settings.onfloor == 0 and not settings.draging


class AccessoryFollowTests(unittest.TestCase):
    def test_accessory_catches_up_after_main_lands(self):
        with mock.patch.multiple(
            settings,
            set_fall=1,
            onfloor=0,
            draging=0,
            tunable_scale=1,
            create=True,
        ):
            accessory = FakeAccessory()
            QAccessory.update_main_pos(accessory, 100, 100)

            settings.onfloor = 1
            QAccessory.update_main_pos(accessory, 100, 100)

            self.assertEqual(accessory.position, [60, 70])
            self.assertTrue(accessory.recovering_from_fall)
            self.assertFalse(accessory.at_destination)

            for _ in range(100):
                if accessory.at_destination:
                    break
                QAccessory.move_to_main(accessory)

            self.assertEqual(accessory.position, [110, 120])
            self.assertFalse(accessory.recovering_from_fall)
            self.assertTrue(accessory.at_destination)


if __name__ == '__main__':
    unittest.main()
