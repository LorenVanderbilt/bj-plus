-- Tuning aid (no ROM change kept): the boomerang's reach, trip time and size, live, from the settings below, so
-- they can be felt in play before a patch fixes them. Its flight (0x47780-0x4793C): a loop round a point ahead of
-- the thrower - the point LOOP[level] out (0x4793E), the radius that + 0x800; forward throws an oval, wide and flat
-- (up throws tall) - starting at the thrower's side, the angle stepping 0x0A00 a frame, gone after one turn.
-- Settings (environment variables; any left out keep the build's):
--   REACH1 REACH2 REACH3  how far it goes out at each level, px ahead of Blue (the build: 44 / 65 / 73)
--   FRAMES                frames for the whole trip, out and back (the build: 26)
--   SIZE1 SIZE2 SIZE3     its size at each level, % (the build: 100 / 88 / 88 - levels 2 and 3 share a drawing)
-- e.g. REACH2=90 FRAMES=40 SIZE2=100 ./run.sh -- -state boomerang -autoboot_script tools/probes/boomerang_tune.lua
-- (gives the boomerang too, at LEVEL - default 2 - like give_boomerang.lua; D switches to it)
local m = manager.machine
local mem = m.devices[":maincpu"].spaces["program"]
local function num(name) return tonumber(os.getenv(name) or "") end
local LEVEL = num("LEVEL") or 2
local LOOP = 0x4793E
local CODE_LO, CODE_HI = 0x4770A, 0x47990
-- reach px = LOOP / 128 + (LOOP + 0x800) / 256  ->  LOOP = (reach - 8) * 256 / 3
for lv = 1, 3 do
  local r = num("REACH" .. lv)
  if r then mem:write_direct_u16(LOOP + 2 * lv, math.max(0, math.floor((r - 8) * 256 / 3))) end
end
local frames = num("FRAMES")
if frames then
  local step = math.floor(65536 / frames)
  for a = 0x47780, 0x478A6, 2 do                   -- its angle steps: move.w #0x0A00 / #0xF600,0x3E(a5)
    if mem:read_u16(a) == 0x3B7C and mem:read_u16(a + 4) == 0x003E then
      local v = mem:read_u16(a + 2)
      mem:write_direct_u16(a + 2, (v >= 0x8000) and ((0x10000 - step) & 0xFFFF) or step)
    end
  end
end
local size = {}
for lv = 1, 3 do local s = num("SIZE" .. lv) if s then size[lv] = math.max(1, math.min(255, math.floor(s * 255 / 100))) end end
local k = 0
SUB = emu.add_machine_frame_notifier(function()
  k = k + 1
  if k >= 20 and k <= 22 then                      -- the boomerang in hand (as give_boomerang.lua)
    mem:write_u8(0x10702B, LEVEL) mem:write_u8(0x10702C, 0)
    mem:write_u8(0x1073F1, LEVEL) mem:write_u8(0x1073F2, 0)
  end
  if next(size) then
    local lv = mem:read_u8(0x10702B)
    if size[lv] then
      for i = 1, 63 do
        local a = 0x104000 + i * 0x80
        local c = mem:read_u32(a + 4) & 0xFFFFFF
        if c >= CODE_LO and c < CODE_HI then mem:write_u8(a + 0x26, size[lv]) mem:write_u8(a + 0x27, size[lv]) end
      end
    end
  end
end)
