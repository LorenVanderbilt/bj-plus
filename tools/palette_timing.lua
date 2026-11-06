-- Run by tools/palette_timing.py: logs every palette RAM write (0x400000-0x401FFF) by its writer's PC, with how
-- many there were, how many landed on the picture's lines (16-239) and the first and last TV line seen. Negative
-- lines are in the vblank. MAME 0.289's screen has no vpos(), so the line comes from the time to the next vblank.
local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]
local scr = manager.machine.screens[":screen"]
local stats, frames = {}, 0

local function line()
  return math.floor(240 - scr:time_until_vblank_start():as_double() / scr.scan_period)
end

local function write(offset)
  local pc, l = cpu.state["PC"].value, line()
  local s = stats[pc]
  if not s then
    s = {n = 0, seen = 0, first = l, last = l}
    stats[pc] = s
  end
  s.n = s.n + 1
  if l >= 16 and l <= 239 then s.seen = s.seen + 1 end
  if l < s.first then s.first = l end
  if l > s.last then s.last = l end
end

-- Loading a save remaps the memory, which drops a tap made before it: the tap goes in on the second frame.
SUB = emu.add_machine_frame_notifier(function()
  frames = frames + 1
  if frames == 2 then TAP = mem:install_write_tap(0x400000, 0x401FFF, "palette_timing", write) end
end)

STOP = emu.add_machine_stop_notifier(function()
  local f = io.open(os.getenv("PALETTE_TIMING_OUT"), "w")
  for pc, s in pairs(stats) do f:write(string.format("%06X %d %d %d %d\n", pc, s.n, s.seen, s.first, s.last)) end
  f:close()
end)
