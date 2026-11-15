import unittest
from datetime import date, timedelta

from DyberPet.aec import (
    AECEventCatalog,
    AECProgression,
    get_work_badge_label,
    get_work_display_state,
    migrate_aec_progression,
    parse_running_work_apps,
    resolve_work_profiles,
)
from DyberPet.conf import migrate_role_mapping, migrate_role_name


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
    def test_role_rename_migrates_legacy_data(self):
        role_data = {'TamatectAEC': {'legacy': True}}

        migrate_role_mapping(role_data)

        self.assertEqual(role_data, {'Tamatect': {'legacy': True}})
        self.assertEqual(migrate_role_name('TamatectAEC'), 'Tamatect')

    def test_role_rename_migrates_keys_without_overwriting_new_values(self):
        role_data = {
            'TamatectAEC': {'legacy': True},
            'Tamatect': {'current': True},
        }

        migrate_role_mapping(role_data)

        self.assertNotIn('TamatectAEC', role_data)
        self.assertEqual(role_data['Tamatect'], {'current': True})

    def test_work_grants_exp_and_costs_health(self):
        progression = AECProgression(FakePetData())
        results = [progression.work_minute() for _ in range(25)]

        self.assertEqual(sum(exp_gain for _, exp_gain, _ in results), 25)
        self.assertEqual(results[-1][0], -1)
        self.assertEqual(sum(health_change for health_change, _, _ in results), -1)
        self.assertEqual(sum(coins for _, _, coins in results), 625)

    def test_overwork_reduces_exp_rate(self):
        pet_data = FakePetData({
            'work_minutes_today': 120,
            'work_date': date.today().isoformat(),
            'exp_remainder': 0.0,
        })
        progression = AECProgression(pet_data)

        results = [progression.work_minute() for _ in range(2)]

        self.assertEqual(sum(exp_gain for _, exp_gain, _ in results), 1)
        self.assertEqual(pet_data.aec_data['work_minutes_today'], 122)

    def test_work_counter_resets_on_new_day(self):
        pet_data = FakePetData({
            'work_minutes_today': 200,
            'work_date': (date.today() - timedelta(days=1)).isoformat(),
            'exp_remainder': 0.5,
        })
        progression = AECProgression(pet_data)

        _, exp_gain, _ = progression.work_minute()

        self.assertEqual(exp_gain, 1)
        self.assertEqual(pet_data.aec_data['work_minutes_today'], 1)
        self.assertEqual(pet_data.aec_data['exp_remainder'], 0.0)

    def test_revit_keeps_fractional_coins_and_doubles_health_loss(self):
        pet_data = FakePetData()
        progression = AECProgression(pet_data)

        results = [
            progression.work_minute(('revit',))
            for _ in range(25)
        ]

        self.assertEqual(sum(health for health, _, _ in results), -2)
        self.assertEqual(sum(coins for _, _, coins in results), 937)
        self.assertEqual(pet_data.aec_data['coin_remainder'], 0.5)

    def test_detected_rhino_and_revit_rewards_stack(self):
        pet_data = FakePetData()
        progression = AECProgression(pet_data)

        health, exp, coins = progression.work_minute(
            ('rhino', 'revit'), detected=True)

        self.assertEqual((health, exp, coins), (0, 2, 187))
        self.assertEqual(pet_data.aec_data['coin_remainder'], 0.5)
        self.assertEqual(pet_data.aec_data['health_remainder'], 2.0)
        self.assertEqual(pet_data.aec_data['work_minutes_today'], 2)

    def test_tasklist_process_names_are_matched_case_insensitively(self):
        output = (
            '"Image Name","PID","Session Name","Session#","Mem Usage"\r\n'
            '"Rhino.exe","123","Console","1","1,000 K"\r\n'
            '"REVIT.EXE","456","Console","1","2,000 K"\r\n'
            '"notepad.exe","789","Console","1","3,000 K"\r\n'
        )

        self.assertEqual(
            parse_running_work_apps(output),
            frozenset(('rhino', 'revit')),
        )

    def test_manual_work_mode_overrides_detected_applications(self):
        self.assertEqual(
            resolve_work_profiles(
                'rhino', frozenset(('rhino', 'revit')), focus_working=True),
            (('rhino',), False),
        )

    def test_auto_work_mode_combines_detected_applications(self):
        self.assertEqual(
            resolve_work_profiles(
                'auto', frozenset(('rhino', 'revit'))),
            (('rhino', 'revit'), True),
        )

    def test_focus_task_defaults_to_manual_rhino_when_auto_detecting(self):
        self.assertEqual(
            resolve_work_profiles('auto', frozenset(), focus_working=True),
            (('rhino',), False),
        )

    def test_work_badge_distinguishes_focus_and_work_profiles(self):
        self.assertEqual(
            get_work_badge_label('auto', 'rhino', True, frozenset()),
            'Focus',
        )
        self.assertEqual(
            get_work_badge_label(
                'auto', 'with_revit', True, frozenset(('revit',))),
            'Working with you in Revit',
        )
        self.assertEqual(
            get_work_badge_label(
                'auto', 'hard_revit', False, frozenset(('revit',))),
            'Working hard in Revit',
        )
        self.assertEqual(
            get_work_badge_label(
                'auto', 'with_rhino', True, frozenset(('rhino',))),
            'Working with you in Rhino',
        )
        self.assertEqual(
            get_work_badge_label('rhino', 'hard_rhino', False, frozenset()),
            'Working hard in Rhino',
        )
        self.assertEqual(
            get_work_badge_label(
                'auto', 'rhino_inside', False, frozenset(('rhino', 'revit'))),
            'working with you on Rhino.Inside',
        )
        self.assertIsNone(
            get_work_badge_label('auto', None, False, frozenset()),
        )

    def test_work_display_state_matches_detected_apps_and_focus_state(self):
        cases = [
            ('auto', frozenset(('rhino',)), False, 'hard_rhino'),
            ('auto', frozenset(('rhino',)), True, 'with_rhino'),
            ('auto', frozenset(('revit',)), False, 'hard_revit'),
            ('auto', frozenset(('revit',)), True, 'with_revit'),
            ('auto', frozenset(('rhino', 'revit')), False, 'rhino_inside'),
            ('auto', frozenset(), True, None),
            ('revit', frozenset(), False, 'hard_revit'),
        ]
        for work_mode, detected_apps, focus_working, expected in cases:
            with self.subTest(
                    work_mode=work_mode,
                    detected_apps=detected_apps,
                    focus_working=focus_working):
                self.assertEqual(
                    get_work_display_state(
                        work_mode, detected_apps, focus_working),
                    expected,
                )

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

    def test_periodic_events_roll_at_the_configured_work_interval(self):
        catalog = AECEventCatalog([{
            'id': 'bim_crash',
            'name': 'BIM model crash',
            'interval_minutes': 15,
            'chance': 0.01,
        }])

        self.assertEqual(
            catalog.roll_periodic_events(14, random_value=lambda: 0.005),
            [],
        )
        self.assertEqual(
            catalog.roll_periodic_events(15, random_value=lambda: 0.005),
            ['bim_crash'],
        )
        self.assertEqual(
            catalog.roll_periodic_events(30, random_value=lambda: 0.01),
            [],
        )

    def test_periodic_event_schedule_requires_valid_probability_and_interval(self):
        for definition in (
                {'interval_minutes': 0, 'chance': 0.01},
                {'interval_minutes': 15, 'chance': 1.01},
                {'chance': 0.01}):
            with self.subTest(definition=definition):
                with self.assertRaises(ValueError):
                    AECEventCatalog([{
                        'id': 'invalid',
                        'name': 'Invalid',
                        **definition,
                    }])


if __name__ == '__main__':
    unittest.main()
