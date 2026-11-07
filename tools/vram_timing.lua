-- Run by tools/vram_timing.py: logs VRAM accesses made faster than the real LSPC allows (SNK's minimums, from the
-- NeoGeo Dev Wiki's VRAM page): a read of REG_VRAMRW sooner than 16 CPU cycles after REG_VRAMADDR is set, a new
-- address sooner than 16 after a data write, and a data write sooner than 12 after the last one. MAME and FBNeo
-- don't enforce them; the console returns stale data or drops the access. Each is logged by the PC after the
-- access (the tap sees the CPU's prefetch), with how many times and the shortest gap seen.
local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]
local clock = 12000000                 -- the 68000 (this MAME's Lua has no clock field)
local stats, frames = {}, 0
local last_addr, last_data = -1, -1     -- times (in cycles) of the last address set / data write

local function now()
  return manager.machine.time:as_double() * clock
end

local function note(kind, gap, need)
  if gap >= need - 0.5 then return end      -- (MAME's timestamps land just under a whole cycle)
  local key = string.format("%s %06X", kind, cpu.state["PC"].value)
  local s = stats[key]
  if not s then
    s = {n = 0, least = gap}
    stats[key] = s
  end
  s.n = s.n + 1
  if gap < s.least then s.least = gap end
end

local function write(offset)
  local t = now()
  if offset == 0x3C0000 then
    note("addr-after-write", t - last_data, 16)
    last_addr = t
  elseif offset == 0x3C0002 then
    note("write-after-write", t - last_data, 12)
    last_data = t
  end
end

local function read(offset)
  if offset == 0x3C0002 then note("read-after-addr", now() - last_addr, 16) end
end

-- Loading a save remaps the memory, which drops a tap made before it: the taps go in on the second frame.
SUB = emu.add_machine_frame_notifier(function()
  frames = frames + 1
  if frames == 2 then
    WTAP = mem:install_write_tap(0x3C0000, 0x3C0003, "vram_timing_w", function(o) pcall(write, o) end)
    RTAP = mem:install_read_tap(0x3C0000, 0x3C0003, "vram_timing_r", function(o) pcall(read, o) end)
  end
end)

STOP = emu.add_machine_stop_notifier(function()
  local f = io.open(os.getenv("VRAM_TIMING_OUT"), "w")
  for key, s in pairs(stats) do f:write(string.format("%s %d %.1f\n", key, s.n, s.least)) end
  f:close()
end)
