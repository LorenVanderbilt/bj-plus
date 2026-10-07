-- Preview only (no ROM change): a checkerboard reveal as a level appears. Load any level save with this script:
--   ./run.sh -- -state <save> -autoboot_script tools/probes/checker_preview.lua
-- The fix layer (drawn over everything) is covered with black, then uncovered in 16 px squares: a diagonal
-- sweep of one colour of the checkerboard, then the other. The fix layer's own contents (the HUD) are saved first
-- and put back square by square. It plays once on load; reload the save to see it again.
local SQUARE = 2            -- fix cells (8 px) a square
local START = 10            -- frames of black before the reveal
local STEP = 1              -- frames between diagonals
local SECOND = 10           -- frames after the first colour's sweep starts that the second's starts
local mem
local saved = {}
local black
local n = 0
local function vr(a) mem:write_u16(0x3C0000, a) return mem:read_u16(0x3C0002) end
local function vw(a, v) mem:write_u16(0x3C0000, a) mem:write_u16(0x3C0002, v) end
local function cell(c, r) return 0x7000 + c * 32 + r end
SUB = emu.register_frame_done(function()
  n = n + 1
  mem = manager.machine.devices[":maincpu"].spaces["program"]
  if n == 1 then
    for c = 0, 39 do for r = 0, 31 do saved[cell(c, r)] = vr(cell(c, r)) end end
    black = mem:read_u16(0x15784 + 12 * 2)     -- the game's own fade's darkest tile (its fade-out table, last step)
  end
  local done = true
  for c = 0, 39 do
    for r = 0, 31 do
      local sx, sy = c // SQUARE, r // SQUARE
      local at = START + (sx + sy) * STEP + ((sx + sy) % 2) * SECOND
      if n < at then vw(cell(c, r), black) done = false
      elseif n == at then vw(cell(c, r), saved[cell(c, r)]) end
    end
  end
  if done and n > START then SUB = nil end
end)
