-- Preview only (no ROM change kept): the travel agent's ride scene with the hardware tile animation clock faster,
-- so its grid (two layers of auto-animated tiles, 4 frames each, palette 0x88) glides instead of stepping.
-- anim-speed / mech-anim-speed set the clock every vblank (9 frames a step outside Mechanical City); this rewrites
-- that speed in the loaded ROM image while the ride's grid is on screen, and puts it back after.
-- SPEED = frames a step (1 = every frame; the original game's was 5, ours 9):
--   SPEED=2 ./run.sh -- -state travel_ticket -autoboot_script tools/probes/ride_grid_preview.lua   (then press A)
local SPEED = tonumber(os.getenv("SPEED") or "2")
local m = manager.machine
local cpu = m.devices[":maincpu"]
local mem = cpu.spaces["program"]
local at                                           -- mech-anim-speed's `or.w #<normal>,d0 ; addq.l #2,sp ; move.w d0,0x3C0006`
for a = 0x80000, 0xFFFF8, 2 do
  if mem:read_u16(a) == 0x0040 and mem:read_u16(a + 4) == 0x548F and mem:read_u16(a + 6) == 0x33C0 then at = a + 2 break end
end
assert(at, "ride_grid_preview: the clock write not found")
local normal = mem:read_u16(at)
local function vr(a) mem:write_u16(0x3C0000, a) return mem:read_u16(0x3C0002) end
SUB = emu.add_machine_frame_notifier(function()
  local ride = false
  for r = 8, 15 do local t = vr(64 + r * 2) if t >= 0x5560 and t <= 0x55BF then ride = true end end   -- a grid tile in layer 1
  mem:write_direct_u16(at, ride and ((SPEED - 1) << 8) or normal)   -- (straight into the ROM image)
end)
