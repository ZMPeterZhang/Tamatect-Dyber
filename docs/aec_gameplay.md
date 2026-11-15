# Tamatect gameplay

Select the `Tamatect` role to enable the AEC loop. It reuses the supplied
numbered PNG frames and the existing focus and Pomodoro timers. Its 300x300
frames are rendered at native size with role scale 1.0.
Settings, pet saves, and custom animation data from the former `TamatectAEC`
role are migrated to `Tamatect`.

- Focus and Pomodoro work minutes grant 1 EXP per minute for the first 120
  work minutes each day, 0.5 EXP per minute through minute 240, then 0.25 EXP
  per minute.
- Every 25 work minutes reduce health by 1 point. Use Sleep from the status
  menu to restore 1 health every five minutes; waking or starting work cancels
  sleep.
- Food continues to restore health through the existing item effects.
- While working, a badge above the pet shows Rhino, Revit, or Focus (for a
  focus-only session). Work uses the `focus` frames, food uses the
  `feed_2`/`eating_ordinary` frames, and sleep uses the `sleep`/`sleeping`
  frame.
- AEC EXP and Level reuse favorability and its level. Existing AEC EXP/Level
  save values are migrated to those fields; non-AEC roles retain their current
  favorability behavior.
- Eating, working, sleeping, and the BIM model crash event use role-configured
  PNG actions. Event definitions can apply Health/EXP effects, play an action,
  and play a role-local sound file from `res/role/<role>/sound/`; Python
  handlers can be registered for behavior that needs code.
- The AEC Debug menu provides Health +/-10 and Level +/-1 controls. AEC level
  drives existing action and item level locks for this role.
- The AEC Hard Hat collection item is awarded at level 0 for immediate Equip
  testing and can be worn as a persistent overlay.
- Existing focus, Pomodoro, task, and item-sale coin rewards are unchanged;
  work grants EXP without adding a second coin payout.

Daily work minutes and fractional EXP are stored alongside each pet's existing
save record. Older save records are given defaults when loaded; HP values are
not converted.

## Placeable items

The status menu's **Edit Items** action manages owned, visible layer items.
Placeable items can be added from the AEC Debug menu with **Add Shop Item…**;
the importer also supports one-use health consumables. Use a collection item
from the Backpack to place or withdraw it. Placeable items use one slot each,
starting with two slots and gaining one per progression level.

Each static layer is stored as a paired PNG and JSON file under
`res/role/<role>/layers/`. The JSON `inventory_item` field links it to the
exact collection name in the role's `items/items_config.json`. The editor
supports repositioning, scaling, flipping, ordering, and withdrawing these
layers. Owned, single-frame `equip` accessories defined by the role's legacy
`accessory_act` configuration are also bridged into editable layers when used.
Animated accessories remain on their existing path. During a fall, equipped
layers follow the pet's recent path with the existing accessory delay and settle
back onto the pet after landing.
