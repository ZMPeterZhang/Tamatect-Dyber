import unittest
from datetime import date, timedelta

from DyberPet.aec import (
    AECEventCatalog,
    AECProgression,
    migrate_aec_progression,
)


class FakePetData:
    def __init__(self, aec_data=None):
        self.aec_data = aec_data or {
            'work_minutes_today': 0,
            'work_date': date.today().isoformat(),
            'exp_remainder': 0.0,
        }

    def change_aec_data(self, **updates):
        self.aec_data.update(updates)


class AECProgressionTests(unittest.TestCase):
    def test_work_grants_exp_and_costs_health(self):
        progression = AECProgression(FakePetData())
        results = [progression.work_minute() for _ in range(25)]

        self.assertEqual(sum(exp_gain for _, exp_gain in results), 25)
        self.assertEqual(results[-1][0], -1)
        self.assertEqual(sum(health_change for health_change, _ in results), -1)

    def test_overwork_reduces_exp_rate(self):
        pet_data = FakePetData({
            'work_minutes_today': 120,
            'work_date': date.today().isoformat(),
            'exp_remainder': 0.0,
        })
        progression = AECProgression(pet_data)

        results = [progression.work_minute() for _ in range(2)]

        self.assertEqual(sum(exp_gain for _, exp_gain in results), 1)
        self.assertEqual(pet_data.aec_data['work_minutes_today'], 122)

    def test_work_counter_resets_on_new_day(self):
        pet_data = FakePetData({
            'work_minutes_today': 200,
            'work_date': (date.today() - timedelta(days=1)).isoformat(),
            'exp_remainder': 0.5,
        })
        progression = AECProgression(pet_data)

        _, exp_gain = progression.work_minute()

        self.assertEqual(exp_gain, 1)
        self.assertEqual(pet_data.aec_data['work_minutes_today'], 1)
        self.assertEqual(pet_data.aec_data['exp_remainder'], 0.0)

    def test_sleep_recovers_health_once_per_five_minutes(self):
        progression = AECProgression(FakePetData())

        self.assertEqual(
            [progression.rest_minute() for _ in range(5)],
            [0, 0, 0, 0, 1],
        )

    def test_migration_moves_legacy_aec_progression_to_favorability(self):
        fv, level, data, migrated = migrate_aec_progression(
            {'exp': 15, 'level': 1, 'work_minutes_today': 4},
            fv=3,
            fv_level=0,
            level_thresholds=[20, 120],
        )

        self.assertTrue(migrated)
        self.assertEqual((fv, level), (15, 1))
        self.assertNotIn('exp', data)
        self.assertNotIn('level', data)

    def test_event_catalog_rejects_unknown_stats(self):
        with self.assertRaises(ValueError):
            AECEventCatalog([{
                'id': 'invalid',
                'name': 'Invalid',
                'effects': {'coins': 1},
            }])

    def test_event_catalog_rejects_sound_paths(self):
        with self.assertRaises(ValueError):
            AECEventCatalog([{
                'id': 'invalid',
                'name': 'Invalid',
                'sound': '../outside.mp3',
            }])


if __name__ == '__main__':
    unittest.main()
