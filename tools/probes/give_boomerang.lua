-- Testing aid: a moment after the save loads, puts player 1's boomerang in hand at level LEVEL and takes the acorn bomb
-- away (weapon-switch's own copies of their levels too), so the boomerang can be tried from any save. The item bar
-- still shows the old weapon: press D (left Shift) to switch round to the boomerang and it updates.
--   ./run.sh -- -state goal_touch -autoboot_script tools/probes/give_boomerang.lua
-- Level 2 instead: BOOMERANG_LEVEL=2 ./run.sh -- -state goal_touch -autoboot_script tools/probes/give_boomerang.lua
local LEVEL = tonumber(os.getenv("BOOMERANG_LEVEL") or "3")
local k = 0
SUB = emu.add_machine_frame_notifier(function()
  k = k + 1
  if k < 20 or k > 22 then return end
  local mem = manager.machine.devices[":maincpu"].spaces["program"]
  mem:write_u8(0x10702B, LEVEL)      -- the boomerang, at LEVEL
  mem:write_u8(0x10702C, 0)          -- no acorn bomb in hand
  mem:write_u8(0x1073F1, LEVEL)      -- (weapon-switch's own copies of their levels)
  mem:write_u8(0x1073F2, 0)
end)
