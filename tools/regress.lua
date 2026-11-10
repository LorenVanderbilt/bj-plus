-- Regression run (tools/regress.py): play a save, take snapshots, and write a report of how the CPU did.
-- REGRESS_REPORT names the report file; the snapshots go to MAME's snapshot directory (0000.png, 0001.png ...; the
-- report's "snaps" line gives each one's frame).
--   a save alone: 5 seconds with the same input every time (HOLD), snapshots at SNAPS
--   REGRESS_CLIP=1: a recorded clip plays the input (MAME -playback); a snapshot every EVERY frames until it ends
dofile("tools/difficulty.lua")        -- (a test played at a difficulty: HACK_DIFFICULTY; nothing otherwise)
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
local WIPE_ON = 0x10EA60               -- stage-wipe's byte: 2 while the iris opens
local COVER_PALETTE = 7                -- its black cover and the iris's edge tiles: fix palette 7
local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]
local joy = manager.machine.ioport.ports[":ctrl1:joy:JOY"]
local frame, faults, pcs, bios, snaps, written = 0, 0, {}, 0, {}, false
local iris_checked, iris_holes, iris_first = 0, 0, 0

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
    h:write(string.format("iris_checked %d\niris_holes %d\niris_first %d\n", iris_checked, iris_holes, iris_first))
    if err then h:write("error " .. tostring(err):gsub("\n", " ") .. "\n") end
    h:close()
end

-- While the iris opens, the cells not under its black cover (any fix palette but COVER_PALETTE) must be one patch
-- touching itself (8 ways round): the opening. A second patch is a hole in the cover - something cleared cells
-- under it (hud-safe-area did, 2026-11-09). Read only while the game waits for the vblank, between its own writes.
local function iris_check()
    if mem:read_u8(WIPE_ON) ~= 2 then return end
    local pc = cpu.state["PC"].value
    if pc < VBLANK_WAIT[1] or pc > VBLANK_WAIT[2] then return end
    local open, seen, patches = {}, {}, 0
    for c = 0, 39 do
        for r = 2, 29 do                                  -- the visible rows
            mem:write_u16(0x3C0000, 0x7000 + c * 32 + r)
            if (mem:read_u16(0x3C0002) >> 12) ~= COVER_PALETTE then open[c * 32 + r] = true end
        end
    end
    for cell in pairs(open) do
        if not seen[cell] then
            patches = patches + 1
            seen[cell] = true
            local todo = {cell}
            while #todo > 0 do
                local at = table.remove(todo)
                for dc = -1, 1 do
                    for dr = -1, 1 do
                        local n = at + dc * 32 + dr
                        if open[n] and not seen[n] then seen[n] = true; todo[#todo + 1] = n end
                    end
                end
            end
        end
    end
    iris_checked = iris_checked + 1
    if patches > 1 then
        iris_holes = iris_holes + 1
        if iris_first == 0 then iris_first = frame end
    end
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
    iris_check()
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
