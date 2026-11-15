import unittest
from collections import deque
from types import SimpleNamespace
from unittest import mock

from PySide6.QtCore import QPoint

from DyberPet import settings
from DyberPet.Accessory import ACCESSORY_FOLLOW_DELAY_MS, ItemLayerFall, QAccessory


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
    def test_item_layers_follow_delayed_positions_and_settle_at_landing(self):
        released = QPoint(100, 60)
        halfway = QPoint(120, 150)
        landed = QPoint(150, 260)
        label = SimpleNamespace(mapToGlobal=mock.Mock(return_value=halfway))
        overlay = SimpleNamespace(
            pet=SimpleNamespace(label=label, isVisible=lambda: True),
            clock=SimpleNamespace(elapsed=mock.Mock(return_value=100)),
            path=deque([(0, released)]),
            landed_at=None,
            move=mock.Mock(),
            stop=mock.Mock(),
            settled=mock.Mock(),
            follow_delay_ms=100,
        )

        with mock.patch.object(settings, 'onfloor', 0, create=True):
            ItemLayerFall.follow(overlay)
            overlay.move.assert_called_with(released)

            landed_at = 100 + overlay.follow_delay_ms
            settings.onfloor = 1
            label.mapToGlobal.return_value = landed
            overlay.clock.elapsed.return_value = landed_at
            ItemLayerFall.follow(overlay)
            overlay.move.assert_called_with(halfway)
            overlay.stop.assert_not_called()

            overlay.clock.elapsed.return_value = landed_at + ACCESSORY_FOLLOW_DELAY_MS
            ItemLayerFall.follow(overlay)
            overlay.move.assert_called_with(landed)
            overlay.stop.assert_called_once()
            overlay.settled.emit.assert_called_once()

    def test_item_layer_fall_randomizes_delay_for_each_fall_start(self):
        overlay = SimpleNamespace(
            pet=SimpleNamespace(
                label=SimpleNamespace(mapToGlobal=mock.Mock(return_value=QPoint(10, 20)))
            ),
            path=deque(),
            landed_at=None,
            setWindowFlag=mock.Mock(),
            move=mock.Mock(),
            clock=SimpleNamespace(start=mock.Mock()),
            timer=SimpleNamespace(start=mock.Mock()),
        )
        delay_variation = ACCESSORY_FOLLOW_DELAY_MS * 0.1
        low_delay = ACCESSORY_FOLLOW_DELAY_MS - delay_variation
        high_delay = ACCESSORY_FOLLOW_DELAY_MS + delay_variation

        with mock.patch.object(settings, 'on_top_hint', True, create=True), mock.patch(
            'DyberPet.Accessory.random.uniform',
            side_effect=[low_delay, high_delay],
        ) as random_delay:
            ItemLayerFall.start(overlay)
            first_delay = overlay.follow_delay_ms
            ItemLayerFall.start(overlay)
            second_delay = overlay.follow_delay_ms

        self.assertEqual((first_delay, second_delay), (low_delay, high_delay))
        self.assertEqual(random_delay.call_args_list, [
            mock.call(low_delay, high_delay),
            mock.call(low_delay, high_delay),
        ])

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
