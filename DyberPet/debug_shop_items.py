import json
from pathlib import Path
import re

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from . import settings


def add_shop_item(pet):
    filename, _ = QFileDialog.getOpenFileName(pet, 'Choose item artwork', '', 'PNG images (*.png)')
    if not filename:
        return
    name, accepted = QInputDialog.getText(pet, 'Add Shop Item', 'Item name')
    if not accepted:
        return
    price, accepted = QInputDialog.getInt(pet, 'Add Shop Item', 'Price in coins', 5, 1, 999999)
    if not accepted:
        return
    category, accepted = QInputDialog.getItem(
        pet, 'Add Shop Item', 'Category', ['Placeable Item', 'Health Consumable'], 0, False)
    if not accepted:
        return
    health = 0
    if category == 'Health Consumable':
        amount, accepted = QInputDialog.getText(pet, 'Health Consumable', 'Health restored per use', text='10')
        if not accepted:
            return
        try:
            health = int(amount)
            if not 1 <= health <= 100:
                raise ValueError
        except ValueError:
            QMessageBox.warning(pet, 'Health Consumable', 'Enter a whole number from 1 to 100.')
            return
    try:
        register_shop_item(pet, name, price, filename, health=health)
    except (OSError, ValueError) as error:
        QMessageBox.warning(pet, 'Add Shop Item', str(error))


def register_shop_item(pet, name, price, filename, *, health=0):
    if type(health) is not int or not 0 <= health <= 100:
        raise ValueError('Health restored must be a whole number from 1 to 100.')
    name = name.strip()
    slug = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
    if not slug or not 0 < price <= 999999:
        raise ValueError('Enter an item name and a price greater than zero.')
    if any(name.casefold() == existing.casefold() for existing in settings.items_data.item_dict):
        raise ValueError('An item already uses that name.')
    image = QImage(filename)
    if image.isNull():
        raise ValueError('The artwork could not be opened.')
    folder = Path(settings.BASEDIR) / 'res' / 'role' / pet.curr_pet_name
    items = folder / 'items'
    layers = folder / 'layers'
    items.mkdir(exist_ok=True)
    if not health:
        layers.mkdir(exist_ok=True)
    catalog_path = items / 'items_config.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf-8-sig')) if catalog_path.exists() else {}
    filename = f'{slug}.png'
    icon = items / filename
    sprite = layers / filename
    placement = layers / f'{slug}.json'
    if any(path.exists() for path in (icon, sprite, placement)):
        raise ValueError('Choose a name that does not conflict with another item’s artwork.')
    catalog[name] = {'image': filename, 'type': 'collection', 'cost': price,
                     'fv_lock': 0, 'pet_limit': [pet.curr_pet_name],
                     'description': 'A placeable item. Uses one placement slot.'}
    if health:
        catalog[name].update(type='consumable', effect_HP=health,
                             description=f'Restores {health} health. Consumed after one use.')
    layout = {'name': name, 'inventory_item': name, 'offset_x': 0, 'offset_y': 0,
              'scale': 1, 'visible': False}
    temporary = catalog_path.with_suffix('.tmp')
    try:
        if not image.save(str(icon), 'PNG'):
            raise OSError('Could not save the item artwork.')
        if not health:
            if not image.save(str(sprite), 'PNG'):
                raise OSError('Could not save the item layer.')
            placement.write_text(json.dumps(layout, indent=2) + chr(10), encoding='utf-8')
        temporary.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + chr(10), encoding='utf-8')
        temporary.replace(catalog_path)
    except OSError:
        for path in ((icon, temporary) if health else (icon, sprite, placement, temporary)):
            path.unlink(missing_ok=True)
        raise
    settings.items_data.init_data()
    pet._load_item_layers(pet.curr_pet_name)
    settings.equipped_item_layers.update({layer['config']['inventory_item']: layer
                                          for layer in pet.item_layers.values()
                                          if layer['config'].get('inventory_item')})
    pet.refresh_bag.emit()
