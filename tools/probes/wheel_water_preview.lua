-- Preview only (no ROM change): the sunken Ferris wheel continued under the water. The water's tiles just below
-- the waterline in the front layer (the strips that hold the wheel) are swapped for the wheel's tiles from just above
-- it, flipped, in tinted copies of its palettes (TINT of the way to the water's colour) - no extra sprites (the
-- waterline already carries ~109 in places: more would be dropped). The hub's cone (an object on the same 16 px grid)
-- is mirrored the same way. Run while riding / walking:
-- ./run.sh -- -state ferris_water2 -autoboot_script tools/probes/wheel_water_preview.lua
local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]
local COLS = 21                                   -- the front layer's strips (stage 8; its slots move - found each frame)
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
local function xof(spr)                          -- a sprite's x: its own, or (stuck) its chain head's + 16 a sprite
  local k = 0
  while (vr(0x8200 + spr - k) & 0x40) ~= 0 and k < 64 do k = k + 1 end
  return ((vr(0x8400 + spr - k) >> 7) + 16*k) % 512
end
local function yof(spr)                          -- its chain head's top (screen y) and height
  local k = 0
  while (vr(0x8200 + spr - k) & 0x40) ~= 0 and k < 64 do k = k + 1 end
  local s3 = vr(0x8200 + spr - k)
  return (496 - (s3 >> 7)) % 512, s3 & 63
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
  -- the front layer: the strip holding wheel tiles and the surface (the far layer has water too, but scrolls slower)
  local layer, rw
  for spr = 1, 200 do
    local h = vr(0x8200 + spr) & 63
    if h >= 16 then
      local wheel, surf = false, nil
      for r = 0, h - 1 do
        local t = vr(spr*64 + r*2)
        if t >= WHEEL_LO and t <= WHEEL_HI then wheel = true end
        if t >= SURFACE_LO and t <= SURFACE_HI then surf = r end
      end
      if wheel and surf then layer, rw = spr, surf break end
    end
  end
  if not layer then return end
  while layer > 1 and (vr(0x8200 + layer) & 0x40) ~= 0 do layer = layer - 1 end
  local top = yof(layer)
  local wly = (top + 16*rw) % 512
  -- the cone's tiles by (x, screen y)
  local cone = {}
  for spr = 1, 380 do
    local t = vr(spr*64)
    if t >= CONE_LO and t <= CONE_HI then
      local x = xof(spr); local cy, h = yof(spr)
      for j = 0, h - 1 do cone[x .. ":" .. ((cy + 16*j) % 512)] = {vr(spr*64 + j*2), vr(spr*64 + j*2 + 1)} end
    end
  end
  for c = 0, COLS-1 do
    local s = layer + c
    local x = xof(s)
    for k = 0, DEPTH-1 do
      local dst = s*64 + (rw + k)*2
      local below = vr(dst)
      if below >= WATER_LO and below <= WATER_HI then
        local src = rw - 1 - k
        local t, a = vr(s*64 + src*2), vr(s*64 + src*2 + 1)
        local cn = cone[x .. ":" .. ((wly - 16*(k+1)) % 512)]
        if cn and TINTED[cn[2] >> 8] then t, a = cn[1], cn[2] end
        local p = a >> 8
        if TINTED[p] and t >= WHEEL_LO and t <= WHEEL_HI then
          vw(dst, t); vw(dst + 1, (TINTED[p] << 8) | ((a & 0xFF) ~ 2))
        end
      end
    end
  end
end)
