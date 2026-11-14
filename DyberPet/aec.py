from datetime import date


WORK_EXP_LIMIT = 120
OVERWORK_EXP_LIMIT = 240
HEALTH_LOSS_INTERVAL = 25
REST_HEAL_INTERVAL = 5


class AECProgression:
    def __init__(self, pet_data):
        self.pet_data = pet_data
        self.rest_minutes = 0

    def work_minute(self):
        data = self.pet_data.aec_data.copy()
        today = date.today().isoformat()
        if data['work_date'] != today:
            data.update(work_date=today, work_minutes_today=0, exp_remainder=0.0)

        data['work_minutes_today'] += 1
        work_minute = data['work_minutes_today']
        if work_minute <= WORK_EXP_LIMIT:
            exp_rate = 1.0
        elif work_minute <= OVERWORK_EXP_LIMIT:
            exp_rate = 0.5
        else:
            exp_rate = 0.25
        data['exp_remainder'] += exp_rate
        exp_gain = int(data['exp_remainder'])
        data['exp_remainder'] -= exp_gain

        self.pet_data.change_aec_data(**data)
        health_change = -1 if work_minute % HEALTH_LOSS_INTERVAL == 0 else 0
        return health_change, exp_gain

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

            self._definitions[event_id] = definition.copy()

    def __getitem__(self, event_id):
        return self._definitions[event_id]

    def __iter__(self):
        return iter(self._definitions.values())

    def __len__(self):
        return len(self._definitions)
