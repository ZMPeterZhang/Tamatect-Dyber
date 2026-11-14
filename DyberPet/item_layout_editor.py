from PySide6.QtCore import QModelIndex, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QDialog, QDialogButtonBox, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QSlider, QVBoxLayout,
)

from . import settings


class LayoutPreview(QLabel):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.origin = None
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(300, 340)

    def position_in_frame(self, event):
        image = self.pixmap()
        return QPointF((event.position().x() - (self.width() - image.width()) / 2),
                       (event.position().y() - (self.height() - image.height()) / 2))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.editor.selected_layer():
            self.origin = self.position_in_frame(event), self.editor.selected_layer()['offset']

    def mouseMoveEvent(self, event):
        if self.origin is not None:
            start, (x, y) = self.origin
            delta = self.position_in_frame(event) - start
            canvas = self.editor.pet.item_canvas
            image = self.pixmap()
            self.editor.move_selected((x + delta.x() * canvas.width() / image.width(),
                                       y + delta.y() * canvas.height() / image.height()))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.origin is not None:
            self.mouseMoveEvent(event)
            self.origin = None


class ItemLayoutEditor(QDialog):
    def __init__(self, pet):
        super().__init__(pet)
        self.pet = pet
        self.setWindowTitle(self.tr('Edit Items'))
        self.setModal(True)
        self.draft = {key: dict(layer) for key, layer in pet.item_layers.items()}
        self.frame = QPixmap(settings.current_img)
        if getattr(settings, 'current_img_mirrored', False):
            self.frame = QPixmap.fromImage(self.frame.toImage().mirrored(True, False))
        layout = QHBoxLayout(self)
        self.preview = LayoutPreview(self)
        layout.addWidget(self.preview)
        controls = QVBoxLayout()
        layout.addLayout(controls)
        controls.addWidget(QLabel(self.tr('Drag to reorder. Top items draw in front.')))
        self.items = QListWidget()
        self.items.setDragDropMode(QAbstractItemView.InternalMove)
        controls.addWidget(self.items)
        order_controls = QHBoxLayout()
        self.bring_forward = QPushButton(self.tr('Bring Forward'))
        self.send_backward = QPushButton(self.tr('Send Backward'))
        order_controls.addWidget(self.bring_forward)
        order_controls.addWidget(self.send_backward)
        controls.addLayout(order_controls)
        self.bring_forward.clicked.connect(lambda: self.move_layer_in_list(-1))
        self.send_backward.clicked.connect(lambda: self.move_layer_in_list(1))
        self.slots = QLabel()
        controls.addWidget(self.slots)
        controls.addWidget(QLabel(self.tr('Level up to unlock one more slot.')))
        controls.addWidget(QLabel(self.tr('Size')))
        self.size = QSlider(Qt.Horizontal)
        controls.addWidget(self.size)
        self.percent = QLabel()
        controls.addWidget(self.percent)
        self.flip = QPushButton(self.tr('Flip Horizontally'))
        self.flip.setCheckable(True)
        self.reset = QPushButton(self.tr('Reset'))
        self.withdraw = QPushButton(self.tr('Withdraw'))
        for button in (self.flip, self.reset, self.withdraw):
            controls.addWidget(button)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        controls.addWidget(buttons)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        self.items.currentItemChanged.connect(self.selection_changed)
        self.items.model().rowsMoved.connect(self.selection_changed)
        self.size.valueChanged.connect(self.resize_selected)
        self.flip.toggled.connect(self.flip_selected)
        self.reset.clicked.connect(self.reset_selected)
        self.withdraw.clicked.connect(self.withdraw_selected)
        for key, layer in reversed(list(self.draft.items())):
            if layer['visible'] and pet._can_edit_layer(layer):
                item = QListWidgetItem(layer['name'])
                item.setData(Qt.UserRole, key)
                self.items.addItem(item)
        if self.items.currentItem() is None:
            self.items.setCurrentRow(0)
        self.selection_changed()

    def selected_layer(self):
        item = self.items.currentItem()
        return self.draft[item.data(Qt.UserRole)] if item else None

    def ordered_layers(self):
        keys = [self.items.item(i).data(Qt.UserRole) for i in reversed(range(self.items.count()))]
        return {key: self.draft[key] for key in keys}

    def move_layer_in_list(self, step):
        row = self.items.currentRow()
        target = row + step
        if row < 0 or not 0 <= target < self.items.count():
            return
        model = self.items.model()
        root = QModelIndex()
        model.moveRow(root, row, root, target + (step > 0))

    def render(self, *_):
        image = self.pet._compose_item_layers(self.frame, self.ordered_layers(),
                                              target_size=self.preview.size())
        selected = self.selected_layer()
        if selected is not None and not image.isNull():
            bounds = self.pet._item_bounds(selected)
            size = selected['scale']
            x, y = selected['offset']
            sx = image.width() / self.pet.item_canvas.width()
            sy = image.height() / self.pet.item_canvas.height()
            outline = QRectF((x + bounds.x() * size) * sx, (y + bounds.y() * size) * sy,
                             bounds.width() * size * sx, bounds.height() * size * sy)
            painter = QPainter(image)
            painter.setPen(QPen(QColor('#4bdcff'), 1, Qt.DashLine))
            painter.drawRect(outline.intersected(QRectF(image.rect()).adjusted(0.5, 0.5, -0.5, -0.5)))
            painter.end()
        self.preview.setPixmap(image)
        self.slots.setText(self.tr('{used}/{limit} slots used').format(used=self.items.count(), limit=self.pet._item_slot_limit()))

    def selection_changed(self, *_):
        layer = self.selected_layer()
        row = self.items.currentRow()
        self.bring_forward.setEnabled(row > 0)
        self.send_backward.setEnabled(0 <= row < self.items.count() - 1)
        for widget in (self.size, self.flip, self.reset, self.withdraw):
            widget.setEnabled(layer is not None)
        if layer is not None:
            self.size.blockSignals(True)
            self.flip.blockSignals(True)
            self.size.setRange(1, self.pet._maximum_item_percent(layer))
            self.size.setValue(round(layer['scale'] * 100))
            self.flip.setChecked(layer['flipped'])
            self.size.blockSignals(False)
            self.flip.blockSignals(False)
            self.percent.setText(f'{self.size.value()}%')
        else:
            self.percent.clear()
        self.render()

    def move_selected(self, offset):
        layer = self.selected_layer()
        if layer is not None:
            layer['offset'] = self.pet._bounded_item_offset(layer, offset)
            self.render()

    def resize_selected(self, percent):
        layer = self.selected_layer()
        if layer is None:
            return
        size = percent / 100
        difference = layer['scale'] - size
        center = self.pet._item_bounds(layer).center()
        x, y = layer['offset']
        layer['scale'] = size
        self.percent.setText(f'{percent}%')
        self.move_selected((x + center.x() * difference, y + center.y() * difference))

    def flip_selected(self, checked):
        layer = self.selected_layer()
        if layer is None:
            return
        left = self.pet._item_bounds(layer).x()
        layer['flipped'] = checked
        x, y = layer['offset']
        self.move_selected((x + (left - self.pet._item_bounds(layer).x()) * layer['scale'], y))

    def reset_selected(self):
        self.size.setValue(min(100, self.size.maximum()))
        layer = self.selected_layer()
        bounds = self.pet._item_bounds(layer)
        size = layer['scale']
        canvas = self.pet.item_canvas
        self.move_selected(((canvas.width() - bounds.width() * size) / 2 - bounds.x() * size,
                            (canvas.height() - bounds.height() * size) / 2 - bounds.y() * size))

    def withdraw_selected(self):
        layer = self.selected_layer()
        if layer is not None:
            layer['visible'] = False
            self.items.takeItem(self.items.currentRow())
            self.selection_changed()

    def save(self):
        ordered = self.ordered_layers()
        ordered.update((key, layer) for key, layer in self.draft.items() if key not in ordered)
        written = []
        for order, (key, layer) in enumerate(ordered.items()):
            original = self.pet.item_layers[key]
            layer['config'] = dict(layer['config'], draw_order=order)
            if not self.pet._write_item_layer(layer):
                for saved in written:
                    self.pet._write_item_layer(saved)
                return
            written.append(original)
        self.pet.item_layers = ordered
        settings.equipped_item_layers = {layer['config']['inventory_item']: layer for layer in ordered.values()
                                         if layer['config'].get('inventory_item')}
        self.pet.set_img()
        board = getattr(QApplication.instance(), 'board', None)
        if board is not None:
            backpack = board.backpackInterface
            if backpack.clctInterface.isVisible():
                backpack.clctInterface.changeButton()
        self.accept()
