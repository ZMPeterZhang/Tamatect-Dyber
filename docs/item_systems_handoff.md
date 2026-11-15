# Tamatect item systems handoff

Feature commits `22783bb` and `fb98401` build on `41dcf70` from `zmpeterzhang-animation-inventory`. If merging is blocked, apply the companion `tamatect-debug-shop-items.patch` from a clean checkout of the animation branch using `git am -3 /path/to/tamatect-debug-shop-items.patch`. The patch includes the PNG assets and the optional DeskBuddy role. If you rebuild manually, retain the target branch’s animations, physics, sprites, and action mappings.

## Placeable items and rendering

- In `DyberPet/DyberPet.py`, `_load_item_layers` pairs each `res/role/<pet>/layers/<id>.json` with its same-stem transparent PNG. Read the canvas width and height from `pet_conf.json`. Use `inventory_item` to match the exact catalog name. The layer records `name`, `offset_x`, `offset_y`, `scale`, `flipped`, `visible`, and `draw_order`. Draw in ascending order.
- `_compose_item_layers` composites visible owned layers over the current frame and uses smooth scaling. Clamp the visible artwork, measured by its alpha bounds, to the character canvas. The Flip button mirrors a single layer. `current_img_mirrored` in `DyberPet/modules.py` mirrors the composite when the character turns. Keep the worker’s existing drag and gravity logic.
- `use_item` toggles an owned placeable between Use and Withdraw without consuming its inventory copy. Reject placements at capacity. `DyberPet/Dashboard/dashboard_widgets.py` reads `settings.equipped_item_layers` to keep the button text current. Existing consumables continue through the original use path.

## Edit Items and level-based slots

- The right-click **Edit Items** action opens `ItemLayoutEditor` in `DyberPet/item_layout_editor.py`. List placed items. The editor uses draft layers with preview dragging, list reordering, a scale slider, Flip, Reset, and Withdraw. Allow up to 500% within the canvas. Reset centers the visible artwork at up to 100%.
- Save writes the draft layer JSON, updates the equipped-layer mapping, and refreshes the pet and inventory. Cancel discards the draft. `_write_item_layer` writes a temporary file before replacing each layer config. The editor attempts to restore earlier writes if a later save fails.
- Use `2 + max(0, settings.get_progression_level())` as the shared limit for inventory-backed desk and character items. Withdrawing frees a slot. Display used slots and refresh the editor at level up.

## Debug shop importer

- Connect **Add Shop Item…** under the existing AEC debug menu to `DyberPet/debug_shop_items.py`. Prompt for PNG, name, price, and either Placeable Item or Health Consumable. Validate names, file collisions, PNG decode, prices from 1 to 999999, and whole-number health amounts from 1 to 100.
- Add the PNG icon and catalog record under `res/role/<pet>/items/`, keyed by item name in `items_config.json`. A placeable record uses `type: collection` and gets a paired layer PNG and config with `inventory_item` set to the catalog name and `visible` false. A health item uses `type: consumable` and `effect_HP`. It uses one inventory copy and no placement slot.
- Replace the catalog via a temporary file, clean up assets written by a failed import, reload `settings.items_data`, reload the pet’s layers, update `settings.equipped_item_layers`, and emit `refresh_bag` to update the shop.

## Verify the combined build

1. Run `python -m unittest discover -s tests`. Check idle, click reaction, and falling after release above the floor in the preview.
2. Place two items at level zero. Verify a third is blocked, then withdraw one and try again. Level up to gain a slot and verify items follow the character when it turns.
3. Drag, scale, flip, reset, reorder, and withdraw in the editor. Confirm Cancel discards changes and Save survives reopening or restarting.
4. Import and buy one item of each category. Verify Use/Withdraw and verify that using the health item changes health and consumes one copy.

Coffee, Onigiri, and changed hard hat and lamp positions were local preview edits. The feature patch includes the original hat and lamp layers.
