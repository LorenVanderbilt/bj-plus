-- Testing aid: a moment after the save loads, puts player 1's leaf in hand at level LEVEL (1-3; default 2), the
-- boomerang and acorn bomb put away (weapon-switch's own copies of the levels too), so the leaf's levels can be tried
-- from any save:
--   ./run.sh -- -state jungle2_platform -autoboot_script tools/probes/give_leaf.lua
--   LEVEL=3 ./run.sh -- -state jungle2_platform -autoboot_script tools/probes/give_leaf.lua
local LEVEL = tonumber(os.getenv("LEVEL") or "2")
local k = 0
SUB = emu.add_machine_frame_notifier(function()
  k = k + 1
  if k < 20 or k > 22 then return end
  local mem = manager.machine.devices[":maincpu"].spaces["program"]
  mem:write_u8(0x107012, LEVEL - 1)    -- the leaf (0-2)
  mem:write_u8(0x10702B, 0)            -- the boomerang, the acorn bomb: not in hand
  mem:write_u8(0x10702C, 0)
  mem:write_u8(0x1073F0, LEVEL - 1)    -- (weapon-switch's own copy of the leaf's level)
end)
