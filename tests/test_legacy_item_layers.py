import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from DyberPet import settings


class LegacyItemLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        from DyberPet.DyberPet import PetWidget

        cls.pet_widget = PetWidget

    def test_legacy_equip_item_is_recognized_and_persisted_as_a_layer(self):
        owner = QWidget()
        owner.resize(300, 340)
        owner.label = QLabel(owner)
        owner.label.setGeometry(0, 40, 300, 300)
        owner.curr_pet_name = 'Tamatect'
        owner.item_canvas = QSize(300, 300)
        owner.item_layers = {}
        artwork = QImage(32, 32, QImage.Format_ARGB32)
        artwork.fill(Qt.transparent)
        artwork.setPixelColor(12, 12, Qt.white)
        image = QPixmap.fromImage(artwork)
        owner.pet_conf = SimpleNamespace(accessory_act={
            'AEC Hard Hat': {
                'acc_type': 'equip',
                'act_list': [],
                'acc_list': [SimpleNamespace(images=[image])],
                'anchor': [-150, -300],
            },
        })
        owner._item_bounds = lambda layer: self.pet_widget._item_bounds(owner, layer)
        owner._maximum_item_percent = lambda layer: self.pet_widget._maximum_item_percent(owner, layer)
        owner._bounded_item_offset = lambda layer, offset: self.pet_widget._bounded_item_offset(owner, layer, offset)
        owner._can_edit_layer = lambda layer: settings.pet_data.items.get(
            layer['config']['inventory_item'], (None, 0))[1] > 0
        owner._placed_item_count = lambda: 0
        owner._item_slot_limit = lambda: 2
        owner._write_item_layer = lambda layer: self.pet_widget._write_item_layer(owner, layer)
        owner.set_img = Mock()

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(
                    settings,
                    'items_data',
                    SimpleNamespace(item_dict={'AEC Hard Hat': {'item_type': 'collection'}}),
                    create=True), \
                    patch.object(settings, 'equipped_item_layers', {}, create=True), \
                    patch.object(settings, 'pet_data',
                                 SimpleNamespace(items={'AEC Hard Hat': (0, 1)}), create=True), \
                    patch.object(settings, 'tunable_scale', 1, create=True):
                self.pet_widget._load_legacy_accessory_layers(owner)
                layer = next(iter(owner.item_layers.values()))
                layer['path'] = Path(temp_dir) / 'layers' / 'aec_hard_hat_accessory.json'

                self.pet_widget.use_item(owner, 'AEC Hard Hat')

                self.assertEqual(layer['config']['inventory_item'], 'AEC Hard Hat')
                self.assertTrue(layer['visible'])
                self.assertTrue(layer['path'].is_file())
                self.assertTrue(layer['path'].with_suffix('.png').is_file())

    def test_each_visible_item_gets_its_own_fall_overlay(self):
        layers = {
            'first': {'visible': True},
            'second': {'visible': True},
            'hidden': {'visible': False},
        }
        owner = SimpleNamespace(
            item_layers=layers,
            item_layer_falls={},
            _can_edit_layer=lambda layer: True,
            _render_pet_frame=Mock(),
        )
        owner._stop_item_layer_falls = lambda: self.pet_widget._stop_item_layer_falls(owner)
        overlays = []

        def create_overlay(parent):
            overlay = SimpleNamespace(settled=Mock(), start=Mock())
            overlays.append(overlay)
            return overlay

        with patch('DyberPet.DyberPet.ItemLayerFall', side_effect=create_overlay):
            self.pet_widget._start_item_layer_fall(owner)

        self.assertEqual(set(owner.item_layer_falls), {'first', 'second'})
        self.assertEqual(len(overlays), 2)
        for overlay in overlays:
            overlay.settled.connect.assert_called_once_with(owner._render_pet_frame)
            overlay.start.assert_called_once_with()
        owner._render_pet_frame.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
