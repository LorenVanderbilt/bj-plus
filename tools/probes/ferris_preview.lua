-- Preview only (no ROM change): the sunken Ferris wheel's gondolas and its cone drawn "in the water", like the
-- Marsh geysers. Each frame, every gondola's sprite chain (tiles 0x4CBC-0x4CBE) and the cone's (0x4C80) is copied to spare sprites drawn after the
-- water, cut off LINE units below the water's surface: above the line it shows in front of the water, below it
-- the game's own gondola stays hidden behind the water as before.
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local SURFACE = 192          -- the water's top (496 - SCB3 y), from sprites at the waterline in this scene
local LINE = SURFACE + 16    -- cut one tile row below it (as the geysers)
local SPARE = 330            -- first spare sprite used for the copies (the game's sprites end near 161)
local function vr(a) mem:write_u16(0x3C0000, a) return mem:read_u16(0x3C0002) end
local function vw(a, v) mem:write_u16(0x3C0000, a) mem:write_u16(0x3C0002, v) end
SUB = emu.register_frame_done(function()
  local spare = SPARE
  for s = 1, 300 do
    local t = vr(s * 64)
    if ((t >= 0x4CBC and t <= 0x4CBE) or t == 0x4C80) and ((vr(0x8200 + s) >> 6) & 1) == 0 then
      local y3 = vr(0x8200 + s)
      local top = 496 - (y3 >> 7)
      local h = y3 & 63
      local rows = 0
      while rows < h and top + rows * 16 < LINE do rows = rows + 1 end
      local k = 0
      repeat                     -- the chain: this sprite and the sticky ones after it
        local src, dst = s + k, spare + k
        for r = 0, 63 do vw(dst * 64 + r, vr(src * 64 + r)) end
        vw(0x8000 + dst, vr(0x8000 + src))
        if k == 0 then vw(0x8200 + dst, (y3 & ~63 & ~64) | rows) else vw(0x8200 + dst, vr(0x8200 + src)) end
        vw(0x8400 + dst, vr(0x8400 + src))
        k = k + 1
      until ((vr(0x8200 + s + k) >> 6) & 1) == 0
      spare = spare + k
    end
  end
  for s = spare, SPARE + 24 do vw(0x8200 + s, 0) end   -- spare slots not used this frame: hidden
end)
