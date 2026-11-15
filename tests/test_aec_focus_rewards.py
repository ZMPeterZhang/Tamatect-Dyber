import unittest
from types import SimpleNamespace
from unittest import mock

from DyberPet import settings
from DyberPet.Dashboard.dashboard_widgets import FocusPanel


class FocusPanelRewardTests(unittest.TestCase):
    def test_aec_focus_rewards_are_not_paid_twice(self):
        panel = SimpleNamespace(
            addCoins=mock.Mock(),
            tr=lambda text: text,
        )
        with mock.patch.object(
                settings, 'pet_conf',
                SimpleNamespace(aec_mode=True), create=True):
            FocusPanel.reward_coins(panel, 25)

        panel.addCoins.emit.assert_not_called()

    def test_non_aec_focus_reward_rate_is_unchanged(self):
        panel = SimpleNamespace(
            addCoins=mock.Mock(),
            tr=lambda text: text,
        )
        with mock.patch.object(
                settings, 'pet_conf',
                SimpleNamespace(aec_mode=False), create=True):
            FocusPanel.reward_coins(panel, 25)

        panel.addCoins.emit.assert_called_once_with(
            625, True, False, 'Focus task reward:')


if __name__ == '__main__':
    unittest.main()
