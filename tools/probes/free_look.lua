-- Free look: fly Blue around a level as a ghost - no gravity, no walls, no harm - to look the whole map over. The
-- game's own camera follows him, so the level scrolls (and streams in) as in play, and stops at the level's edges.
--   ./run.sh -- -state SAVE -autoboot_script tools/probes/free_look.lua
-- D (left Shift in MAME): ghost on / off - it starts off, so menus and the title work as usual; off again to play
-- normally (e.g. through a door; switch off clear of walls - inside one the game pushes him out, maybe off the
-- screen: a life lost), on again where you are. While on: the joystick flies him (the game doesn't see
-- it), hold A (left Ctrl) to go faster. He's kept on screen: where the camera stops, the level ends.
-- (Testing headless: FREE_LOOK_TEST="R120,U60" holds Right 120 frames, then Up 60, then quits.)
local m = manager.machine
local cpu = m.devices[":maincpu"]
local mem = cpu.spaces["program"]
local HERO_Y, HERO_X = 0x104000, 0x104002     -- (1/128 px; y upwards, screen-relative: the camera follows)
local INVINCIBLE = 0x107009
local TIMER = 0x106904                         -- (the level timer's count, a long: held while flying)
local timer
local P1_NOW, P1_CHANGE = 0x10FD96, 0x10FD97   -- BIOS: joystick / buttons held, newly pressed
local SLOW, FAST = 3, 10                       -- px a frame
local on, held, was_d = os.getenv("FREE_LOOK_TEST") ~= nil, 0, false   -- (off until D: menus work as usual)
local CAM_X, CAM_Y = 0x100216, 0x10020A       -- the camera, px (level x = (x field - 0x4000) / 128 + camera x;
local lx, ly                                   -- level y = -(y field / 128 + camera y)) - his place kept here
local X_MIN, X_MAX = 0x4800, 0xD000            -- (the fields' range that keeps him on screen)
local Y_MIN, Y_MAX = 0x5000, 0xA400
local function s16(v) return v >= 0x8000 and v - 0x10000 or v end

-- the BIOS's joystick bytes: kept for us, hidden from the game while flying (D always gets through to us)
TAP = mem:install_write_tap(P1_NOW, P1_CHANGE, "free_look", function(off, data, mask)
  if off == P1_NOW then
    if mask & 0xFF00 ~= 0 then held = (data >> 8) & 0xFF end
    if on then return 0 end
  elseif off == P1_CHANGE and on then
    return 0
  end
end)

-- the tile type under him (+0x44: lava, a pit, spikes ... kill him whatever his invincibility): plain while flying
TILE_TAP = mem:install_write_tap(0x104044, 0x104045, "free_look_tile", function(off, data, mask)
  if on and mask & 0xFF00 ~= 0 then return data & 0x00FF end
end)

-- his state as the game sets it: kept airborne (3) - the camera follows him up and down only then
STATE_TAP = mem:install_write_tap(0x104068, 0x104069, "free_look_state", function(off, data, mask)
  if on and mask & 0xFF00 ~= 0 and (data >> 8) ~= 3 then return (3 << 8) | (data & 0xFF) end
end)
-- his height as the game sets it mid-frame (a camera jump can drop him far below the screen: a fall to his death)
-- kept on screen too
POS_TAP = mem:install_write_tap(HERO_Y, HERO_Y + 1, "free_look_y", function(off, data, mask)
  if on and mask == 0xFFFF then return math.max(Y_MIN, math.min(Y_MAX, data)) end
end)

-- no walls for him: while the object loop runs his code (from its read of his code pointer, +4, to its look at the
-- next object, 0x104080's +0x28) the level's tiles the collision routines read from VRAM come back empty - so the
-- game never pushes him out of a wall (inside a big one it pushed him off the screen: gone, a life lost)
local in_hero = false
HERO_CODE_TAP = mem:install_read_tap(0x104004, 0x104005, "free_look_in", function(off, data, mask)
  if cpu.state["PC"].value < 0xA200 then in_hero = true end
end)
NEXT_OBJ_TAP = mem:install_read_tap(0x1040A8, 0x1040A9, "free_look_out", function(off, data, mask)
  in_hero = false
end)
VRAM_TAP = mem:install_read_tap(0x3C0002, 0x3C0003, "free_look_vram", function(off, data, mask)
  if on and in_hero then
    local pc = cpu.state["PC"].value
    if pc >= 0xD900 and pc < 0xDB00 then return 0 end
  end
end)

local test, step, left = nil, 1, 0
local spec = os.getenv("FREE_LOOK_TEST")
if spec then
  test = {}
  for dir, n in spec:gmatch("(%a)(%d+)") do test[#test + 1] = {dir, tonumber(n)} end
  left = test[1][2]
end
local BITS = {U = 1, D = 2, L = 4, R = 8}

local frame = 0
SUB = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  local joy = held
  if test then
    if frame < 30 then return end
    local cur = test[step]
    if not cur then print(string.format("free_look: done, hero y %04X x %04X, camera x %d y %d, level x %s y %s, state %d",
      mem:read_u16(HERO_Y), mem:read_u16(HERO_X), mem:read_u16(CAM_X), mem:read_u16(CAM_Y), lx, ly, mem:read_u8(0x104068)))
      m.video:snapshot(); m:exit() return end
    joy = BITS[cur[1]] or 0
    left = left - 1
    if left <= 0 then step = step + 1; if test[step] then left = test[step][2] end end
  end
  local d = joy & 0x80 ~= 0
  if d and not was_d then on = not on; lx = nil; timer = nil end
  was_d = d
  if not on then return end
  mem:write_u8(INVINCIBLE, 0x40)
  timer = timer or mem:read_u32(TIMER)
  mem:write_u32(TIMER, timer)
  local cx, cy = s16(mem:read_u16(CAM_X)), s16(mem:read_u16(CAM_Y))
  if not lx then
    lx = (mem:read_u16(HERO_X) - 0x4000) / 128 + cx
    ly = -(s16(mem:read_u16(HERO_Y)) / 128 + cy)
  end
  local speed = (joy & 0x10 ~= 0) and FAST or SLOW
  if joy & 1 ~= 0 then ly = ly - speed end
  if joy & 2 ~= 0 then ly = ly + speed end
  if joy & 4 ~= 0 then lx = lx - speed end
  if joy & 8 ~= 0 then lx = lx + speed end
  -- kept on screen (where the camera stops - the level's edge - he stops too; off screen he'd die)
  local fx = math.max(X_MIN, math.min(X_MAX, math.floor((lx - cx) * 128 + 0x4000)))
  local fy = math.max(Y_MIN, math.min(Y_MAX, math.floor((-ly - cy) * 128)))
  lx, ly = (fx - 0x4000) / 128 + cx, -(fy / 128 + cy)
  mem:write_u16(HERO_X, fx)
  mem:write_u16(HERO_Y, fy)
  if os.getenv('FL_LOG') and frame % (tonumber(os.getenv('FL_LOG')) or 10) == 0 then print(string.format('f%d st%d y%04X x%04X cam %d %d  l %s %s', frame, mem:read_u8(0x104068), mem:read_u16(HERO_Y), mem:read_u16(HERO_X), cx, cy, lx, ly)) end
end)
