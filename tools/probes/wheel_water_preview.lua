-- Preview only (no ROM change): the sunken Ferris wheel continued under the water. The water's tiles just below
-- the waterline in the front layer (the strips that hold the wheel) are swapped for the wheel's tiles from just above
-- it, flipped, in tinted copies of its palettes (TINT of the way to the water's colour) - no extra sprites (the
-- waterline already carries ~109 in places: more would be dropped). The hub's cone (an object on the same 16 px grid)
-- is mirrored the same way, and the water patches over dipping gondolas (3-tile objects) get the same tiles.
-- Run while riding / walking:
-- ./run.sh -- -state ferris_water2 -autoboot_script tools/probes/wheel_water_preview.lua
--
-- The front layer is one sticky chain of strips; the game redraws its columns as it scrolls, sometimes only the
-- cells that changed. So every cell written here is remembered (what was there, what was written): a cell that no
-- longer holds what was written has been redrawn by the game, and one whose wheel tile above has gone is put back.
local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]
local TINTED = {[0xF9]=0xBC, [0xFA]=0xBD, [0xFB]=0xBE}   -- wheel / cone palette -> its tinted copy (unused in the stage)
local SURFACE_LO, SURFACE_HI, SURF_PAL = 0x2E0, 0x2E7, 0x8F
local WATER_LO, WATER_HI = 0x2E0, 0x2EF          -- the water's tiles (surface row and below)
local WHEEL_LO, WHEEL_HI = 0x4C80, 0x4CFF        -- the wheel's own tiles (not the plants in its palettes)
local CONE_LO, CONE_HI = 0x4C80, 0x4C82          -- the hub's cone (an object)
local TINT = tonumber(os.getenv("TINT") or "0.5")
local DEPTH = 3                                  -- rows below the waterline
local function vr(a) mem:write_u16(0x3C0000, a) return mem:read_u16(0x3C0002) end
local function vw(a, v) mem:write_u16(0x3C0000, a) mem:write_u16(0x3C0002, v) end
local function rgb(w) return ((w>>7)&0x1E)|((w>>14)&1), ((w>>3)&0x1E)|((w>>13)&1), ((w<<1)&0x1E)|((w>>12)&1) end
local function neo(r,g,b) return ((r&1)<<14)|((g&1)<<13)|((b&1)<<12)|((r>>1)<<8)|((g>>1)<<4)|(b>>1) end
local function head(spr)                         -- a sprite's chain head (sticky sprites take its y and x + 16 each)
  local k = 0
  while (vr(0x8200 + spr - k) & 0x40) ~= 0 and k < 64 do k = k + 1 end
  return spr - k
end
local function xof(spr) local h = head(spr) return ((vr(0x8400 + h) >> 7) + 16*(spr - h)) % 512 end
local function yof(spr)                          -- its chain head's top (screen y) and height
  local s3 = vr(0x8200 + head(spr))
  return (496 - (s3 >> 7)) % 512, s3 & 63
end

local mine = {}                                  -- VRAM address of a tile word -> {original tile, attr, written tile, attr}
local function put(at, t, a)
  local m = mine[at]
  if m and (vr(at) ~= m[3] or vr(at + 1) ~= m[4]) then m = nil; mine[at] = nil end   -- the game redrew it
  if not m then
    if not t then return end
    m = {vr(at), vr(at + 1)}; mine[at] = m
  end
  if not t then t, a = m[1], m[2]; mine[at] = nil end                                 -- nothing to show: put back
  if vr(at) ~= t or vr(at + 1) ~= a then vw(at, t); vw(at + 1, a) end
  if mine[at] then m[3], m[4] = t, a end
end

SUB = emu.register_frame_done(function()
  local pc = cpu.state["PC"].value               -- only while the game waits for the vblank: not mid its own writes
  if pc < 0xE856 or pc > 0xE8B2 then return end
  local wr, wg, wb = rgb(mem:read_u16(0x400000 + SURF_PAL*32 + 6*2))
  for src, dst in pairs(TINTED) do
    for c = 1, 15 do
      local r, g, b = rgb(mem:read_u16(0x400000 + src*32 + c*2))
      mem:write_u16(0x400000 + dst*32 + c*2, neo(math.floor(r + (wr-r)*TINT + 0.5), math.floor(g + (wg-g)*TINT + 0.5),
                                                 math.floor(b + (wb-b)*TINT + 0.5)))
    end
  end
  -- the front layer: the chain whose strips hold wheel tiles above the water's surface row
  local first, rw
  for spr = 1, 380 do
    local h = vr(0x8200 + head(spr)) & 63
    if h >= 16 then
      local wheel = false
      for r = 0, math.min(h, 32) - 1 do
        local t = vr(spr*64 + r*2)
        if t >= WHEEL_LO and t <= WHEEL_HI then wheel = true end
        if wheel and t >= SURFACE_LO and t <= SURFACE_HI then first, rw = spr, r break end
      end
      if first then break end
    end
  end
  if not first then return end
  local top = yof(first)
  local wly = (top + 16*rw) % 512                -- the waterline's screen y
  local strips = {head(first)}
  while (vr(0x8200 + strips[#strips] + 1) & 0x40) ~= 0 and #strips < 64 do strips[#strips + 1] = strips[#strips] + 1 end
  -- the cone's tiles by (x, screen y)
  local cone = {}
  for spr = 1, 380 do
    local t = vr(spr*64)
    if t >= CONE_LO and t <= CONE_HI then
      local x = xof(spr); local cy, h = yof(spr)
      for j = 0, h - 1 do cone[x .. ":" .. ((cy + 16*j) % 512)] = {vr(spr*64 + j*2), vr(spr*64 + j*2 + 1)} end
    end
  end
  local shown = {}                               -- x:row -> the reflection's tile and attr there (for the patches)
  for _, s in ipairs(strips) do
    local x = xof(s)
    for k = 0, DEPTH-1 do
      local dst = s*64 + (rw + k)*2
      local m = mine[dst]
      local below = (m and vr(dst) == m[3]) and m[1] or vr(dst)        -- what the game has there
      local t, a
      if below >= WATER_LO and below <= WATER_HI then
        local src = rw - 1 - k
        local st, sa = vr(s*64 + src*2), vr(s*64 + src*2 + 1)
        local sm = mine[s*64 + src*2]
        if sm and st == sm[3] then st, sa = sm[1], sm[2] end
        local cn = cone[x .. ":" .. ((wly - 16*(k+1)) % 512)]
        if cn and TINTED[cn[2] >> 8] then st, sa = cn[1], cn[2] end
        local p = sa >> 8
        if TINTED[p] and st >= WHEEL_LO and st <= WHEEL_HI then
          -- bits 4-7 are the game's collision type (the front layer is its collision map): the water's are kept
          local keep = ((m and vr(dst) == m[3]) and m[2] or vr(dst + 1)) & 0xF0
          t, a = st, (TINTED[p] << 8) | keep | ((sa & 0x0F) ~ 2)
          shown[x .. ":" .. k] = {t, (TINTED[p] << 8) | ((sa & 0x0F) ~ 2)}
        end
      end
      put(dst, t, a)
    end
  end
  -- the water patches over dipping gondolas: 3-tile objects of surface water on the waterline
  for spr = 1, 380 do
    local y, h = yof(spr)
    if h == DEPTH and y == wly then
      local at = spr*64
      local m = mine[at]
      local t0 = (m and vr(at) == m[3]) and m[1] or vr(at)
      local a0 = (m and vr(at) == m[3]) and m[2] or vr(at + 1)
      if t0 >= SURFACE_LO and t0 <= SURFACE_HI and (a0 >> 8) == SURF_PAL then
        local x = xof(spr)
        for k = 0, DEPTH-1 do
          local r = shown[x .. ":" .. k]
          put(at + k*2, r and r[1], r and r[2])
        end
      end
    end
  end
end)
