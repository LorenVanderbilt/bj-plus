-- Testing aid: a moment after the save loads, puts player 1's leaf in hand at its top level (the 3rd: 2 in the
-- player block, 0-2) and takes the acorn bomb and boomerang away (weapon-switch's own copies of the levels too), so
-- the level 3 leaf attack (the tornado) can be tried from any save.
--   ./run.sh -- -state goal_touch -autoboot_script tools/probes/give_leaf.lua
-- Another level: LEVEL=2 (the 2nd - its gust, leaf-gusts) or LEVEL=1 (the basic leaf); or as before, LEAF_LEVEL=1 /
-- 0 (the player block's 0-2).
local LEVEL = tonumber(os.getenv("LEAF_LEVEL") or "") or ((tonumber(os.getenv("LEVEL") or "3")) - 1)
local k = 0
SUB = emu.add_machine_frame_notifier(function()
  k = k + 1
  if k < 20 or k > 22 then return end
  local mem = manager.machine.devices[":maincpu"].spaces["program"]
  mem:write_u8(0x107012, LEVEL)      -- the leaf
  mem:write_u8(0x10702B, 0)          -- the boomerang
  mem:write_u8(0x10702C, 0)          -- the acorn bomb
  mem:write_u8(0x1073F0, LEVEL)      -- (weapon-switch's own copies of the levels)
  mem:write_u8(0x1073F1, 0)
  mem:write_u8(0x1073F2, 0)
end)
