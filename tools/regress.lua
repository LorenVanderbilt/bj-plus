-- Regression run (tools/regress.py): play a save, take snapshots, and write a report of how the CPU did.
-- REGRESS_REPORT names the report file; the snapshots go to MAME's snapshot directory (0000.png, 0001.png ...; the
-- report's "snaps" line gives each one's frame).
--   a save alone: 5 seconds with the same input every time (HOLD), snapshots at SNAPS
--   REGRESS_CLIP=1: a recorded clip plays the input (MAME -playback); a snapshot every EVERY frames until it ends
local REPORT = os.getenv("REGRESS_REPORT")
local CLIP = os.getenv("REGRESS_CLIP") == "1"
local FRAMES = 300
local SNAPS = {30, 150, 300}
local EVERY = 30
local HOLD = {             -- (first frame, last frame, input): walk right, jump twice, attack
    {60, 200, "P1 Right"}, {200, 205, "P1 B"}, {230, 235, "P1 B"}, {260, 265, "P1 A"},
}
local FAULT = {0x47C, 0x490}          -- the game's exception handlers spin here (an odd address, a bad opcode ...)
local VBLANK_WAIT = {0xE8A0, 0xE8B0}   -- where a healthy frame ends: the main loop waiting for the next one
local cpu = manager.machine.devices[":maincpu"]
local joy = manager.machine.ioport.ports[":ctrl1:joy:JOY"]
local frame, faults, pcs, bios, snaps, written = 0, 0, {}, 0, {}, false

local function report(err)
    if written then return end
    written = true
    local h = io.open(REPORT, "w")
    -- stuck: the last second's frames all ended inside one 16-byte stretch of code other than the vblank wait
    -- (the main loop no longer comes round)
    local lo, hi = math.huge, 0
    for i = math.max(1, #pcs - 59), #pcs do lo = math.min(lo, pcs[i]); hi = math.max(hi, pcs[i]) end
    local stuck = #pcs >= 60 and hi - lo < 16 and not (lo >= VBLANK_WAIT[1] and hi <= VBLANK_WAIT[2])
    h:write(string.format("frames %d\nfaults %d\nstuck %d\nbios %d\nlast_pc %06X\nsnaps %s\n", frame, faults,
        stuck and 1 or 0, bios, pcs[#pcs] or 0, table.concat(snaps, " ")))
    if err then h:write("error " .. tostring(err):gsub("\n", " ") .. "\n") end
    h:close()
end

local function snapshot()
    manager.machine.video:snapshot()
    snaps[#snaps + 1] = frame
end

local function step()
    frame = frame + 1
    local pc = cpu.state["PC"].value
    pcs[#pcs + 1] = pc
    if pc >= FAULT[1] and pc <= FAULT[2] then faults = faults + 1 end
    if pc >= 0xC00000 then bios = bios + 1 end        -- frames that ended in the BIOS (a reset lands there)
    if CLIP then
        if frame % EVERY == 0 then snapshot() end     -- (MAME stops at the clip's end: -exit_after_playback)
        return
    end
    for _, h in ipairs(HOLD) do
        joy.fields[h[3]]:set_value((frame >= h[1] and frame <= h[2]) and 1 or 0)
    end
    for _, f in ipairs(SNAPS) do
        if f == frame then snapshot() end
    end
    if frame >= FRAMES then
        report()
        manager.machine:exit()
    end
end

SUB = emu.register_frame_done(function()
    local ok, err = pcall(step)
    if not ok then
        pcall(report, err)
        manager.machine:exit()
    end
end)
STOP = emu.add_machine_stop_notifier(function() report() end)
