import csv
import os
import random
import subprocess
from datetime import date


WORK_EXP_LIMIT = 120
OVERWORK_EXP_LIMIT = 240
HEALTH_LOSS_INTERVAL = 25
REST_HEAL_INTERVAL = 5
WORK_POLL_INTERVAL_MS = 5000
WORK_MINUTE_SECONDS = 60.0
WORK_COIN_RATES = {
    'rhino': 25.0,
    'revit': 37.5,
}
WORK_HEALTH_RATES = {
    'rhino': 1.0,
    'revit': 2.0,
}
DETECTED_WORK_COIN_MULTIPLIER = 3
WORK_PROCESS_NAMES = {
    'rhino.exe': 'rhino',
    'revit.exe': 'revit',
}


def parse_running_work_apps(tasklist_output):
    apps = set()
    for row in csv.reader(tasklist_output.splitlines()):
        if row:
            profile = WORK_PROCESS_NAMES.get(row[0].strip().lower())
            if profile:
                apps.add(profile)
    return frozenset(apps)


def get_running_work_apps():
    if os.name != 'nt':
        return frozenset()

    result = subprocess.run(
        ['tasklist', '/FO', 'CSV', '/NH'],
        check=True,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    )
    return parse_running_work_apps(result.stdout)


def resolve_work_profiles(work_mode, detected_apps, focus_working=False):
    if work_mode in ('rhino', 'revit'):
        return (work_mode,), False
    if work_mode != 'auto':
        raise ValueError(f'Unknown AEC work mode: {work_mode}')

    profiles = tuple(
        profile for profile in ('rhino', 'revit')
        if profile in detected_apps)
    if profiles:
        return profiles, True
    if focus_working:
        return ('rhino',), False
    return (), False


def get_work_badge_label(
        work_mode, display_work_profile, focus_working, detected_apps):
    display_text = {
        'hard_rhino': 'Working hard in Rhino',
        'hard_revit': 'Working hard in Revit',
        'with_rhino': 'Working with you in Rhino',
        'with_revit': 'Working with you in Revit',
        'rhino_inside': 'working with you on Rhino.Inside',
    }.get(display_work_profile)
    if display_text:
        return display_text
    if work_mode == 'auto' and focus_working and not detected_apps:
        return 'Focus'
    return None


def get_work_display_state(work_mode, detected_apps, focus_working=False):
    profiles, detected = resolve_work_profiles(
        work_mode, detected_apps, focus_working)
    if {'rhino', 'revit'}.issubset(detected_apps):
        return 'rhino_inside'
    if work_mode == 'auto' and not detected:
        return None
    if not profiles:
        return None

    activity = 'with' if focus_working else 'hard'
    return f'{activity}_{profiles[0]}'


class AECProgression:
    def __init__(self, pet_data):
        self.pet_data = pet_data
        self.rest_minutes = 0

    def work_minute(self, profiles=('rhino',), detected=False):
        if isinstance(profiles, str):
            profiles = (profiles,)
        profiles = tuple(dict.fromkeys(profiles))
        unknown_profiles = set(profiles) - set(WORK_COIN_RATES)
        if unknown_profiles:
            raise ValueError(f'Unknown AEC work profiles: {sorted(unknown_profiles)}')
        if not profiles:
            return 0, 0, 0

        data = self.pet_data.aec_data.copy()
        today = date.today().isoformat()
        if data['work_date'] != today:
            data.update(
                work_date=today,
                work_minutes_today=0,
                exp_remainder=0.0,
                health_remainder=0.0,
            )

        data.setdefault('exp_remainder', 0.0)
        data.setdefault('coin_remainder', 0.0)
        data.setdefault('health_remainder', 0.0)
        data['exp_remainder'] = max(0.0, float(data['exp_remainder'])) % 1.0
        data['coin_remainder'] = max(0.0, float(data['coin_remainder'])) % 1.0
        data['health_remainder'] = (
            max(0.0, float(data['health_remainder'])) % HEALTH_LOSS_INTERVAL)

        coin_gain = 0
        exp_gain = 0
        for profile in profiles:
            data['work_minutes_today'] += 1
            work_minute = data['work_minutes_today']
            if work_minute <= WORK_EXP_LIMIT:
                exp_rate = 1.0
            elif work_minute <= OVERWORK_EXP_LIMIT:
                exp_rate = 0.5
            else:
                exp_rate = 0.25
            data['exp_remainder'] += exp_rate
            earned_exp = int(data['exp_remainder'])
            data['exp_remainder'] -= earned_exp
            exp_gain += earned_exp

            coin_rate = WORK_COIN_RATES[profile]
            if detected:
                coin_rate *= DETECTED_WORK_COIN_MULTIPLIER
            data['coin_remainder'] += coin_rate
            earned_coins = int(data['coin_remainder'])
            data['coin_remainder'] -= earned_coins
            coin_gain += earned_coins

        health_profile = 'revit' if 'revit' in profiles else profiles[0]
        data['health_remainder'] += WORK_HEALTH_RATES[health_profile]
        health_loss = int(data['health_remainder'] // HEALTH_LOSS_INTERVAL)
        data['health_remainder'] -= health_loss * HEALTH_LOSS_INTERVAL

        self.pet_data.change_aec_data(**data)
        return -health_loss, exp_gain, coin_gain

    def rest_minute(self):
        self.rest_minutes += 1
        if self.rest_minutes % REST_HEAL_INTERVAL == 0:
            return 1
        return 0

    def reset_rest(self):
        self.rest_minutes = 0


def migrate_aec_progression(aec_data, fv, fv_level, level_thresholds):
    data = aec_data.copy()
    if 'exp' not in data and 'level' not in data:
        return fv, fv_level, data, False

    exp = data.pop('exp', fv)
    level = data.pop('level', fv_level)
    if not isinstance(exp, int) or isinstance(exp, bool) or exp < 0:
        exp = 0
    if not isinstance(level, int) or isinstance(level, bool):
        level = fv_level

    level = min(max(level, 0), len(level_thresholds) - 1)
    exp = min(exp, level_thresholds[level])
    return exp, level, data, True


class AECEventCatalog:
    def __init__(self, definitions):
        if not isinstance(definitions, list):
            raise ValueError('AEC events must be a list')

        self._definitions = {}
        for definition in definitions:
            if not isinstance(definition, dict):
                raise ValueError('Each AEC event must be an object')

            event_id = definition.get('id')
            name = definition.get('name')
            if not isinstance(event_id, str) or not event_id:
                raise ValueError('Each AEC event requires a non-empty id')
            if not isinstance(name, str) or not name:
                raise ValueError(f'AEC event {event_id!r} requires a name')
            if event_id in self._definitions:
                raise ValueError(f'Duplicate AEC event id: {event_id}')

            effects = definition.get('effects', {})
            if not isinstance(effects, dict):
                raise ValueError(f'AEC event {event_id!r} effects must be an object')
            for stat, change in effects.items():
                if stat not in ('hp', 'fv'):
                    raise ValueError(f'Unsupported AEC event stat: {stat}')
                if not isinstance(change, int) or isinstance(change, bool):
                    raise ValueError(f'AEC event {event_id!r} effects must be integers')

            animation = definition.get('animation')
            if animation is not None and not isinstance(animation, str):
                raise ValueError(f'AEC event {event_id!r} animation must be a string')

            message = definition.get('message', '')
            if not isinstance(message, str):
                raise ValueError(f'AEC event {event_id!r} message must be a string')

            sound = definition.get('sound')
            if sound is not None and (
                    not isinstance(sound, str) or not sound
                    or '/' in sound or '\\' in sound):
                raise ValueError(
                    f'AEC event {event_id!r} sound must be a filename')

            handler = definition.get('handler')
            if handler is not None and (not isinstance(handler, str) or not handler):
                raise ValueError(f'AEC event {event_id!r} handler must be a non-empty string')

            interval_minutes = definition.get('interval_minutes')
            chance = definition.get('chance')
            if interval_minutes is not None:
                if (not isinstance(interval_minutes, int)
                        or isinstance(interval_minutes, bool)
                        or interval_minutes <= 0):
                    raise ValueError(
                        f'AEC event {event_id!r} interval_minutes must be a positive integer')
                if (not isinstance(chance, (int, float))
                        or isinstance(chance, bool)
                        or not 0 <= chance <= 1):
                    raise ValueError(
                        f'AEC event {event_id!r} chance must be between 0 and 1')
            elif chance is not None:
                raise ValueError(
                    f'AEC event {event_id!r} chance requires interval_minutes')

            self._definitions[event_id] = definition.copy()

    def __getitem__(self, event_id):
        return self._definitions[event_id]

    def __iter__(self):
        return iter(self._definitions.values())

    def __len__(self):
        return len(self._definitions)

    def roll_periodic_events(self, work_minutes, random_value=None):
        if (not isinstance(work_minutes, int)
                or isinstance(work_minutes, bool)
                or work_minutes < 0):
            raise ValueError('work_minutes must be a non-negative integer')
        if random_value is None:
            random_value = random.random

        triggered = []
        for event in self._definitions.values():
            interval_minutes = event.get('interval_minutes')
            if (interval_minutes is not None and work_minutes > 0
                    and work_minutes % interval_minutes == 0
                    and random_value() < event['chance']):
                triggered.append(event['id'])
        return triggered
