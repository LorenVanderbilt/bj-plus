-- Regression run (tools/regress.py): play a save for a few seconds with the same input every time, take snapshots,
-- and write a report of how the CPU did. REGRESS_REPORT names the report file; the snapshots go to MAME's snapshot
-- directory (0000.png, 0001.png ... in SNAPS order).
local REPORT = os.getenv("REGRESS_REPORT")
local FRAMES = 300
local SNAPS = {30, 150, 300}
local HOLD = {             -- (first frame, last frame, input): walk right, jump twice, attack
    {60, 200, "P1 Right"}, {200, 205, "P1 B"}, {230, 235, "P1 B"}, {260, 265, "P1 A"},
}
local FAULT = {0x47C, 0x490}          -- the game's exception handlers spin here (an odd address, a bad opcode ...)
local VBLANK_WAIT = {0xE8A0, 0xE8B0}   -- where a healthy frame ends: the main loop waiting for the next one
local cpu = manager.machine.devices[":maincpu"]
local joy = manager.machine.ioport.ports[":ctrl1:joy:JOY"]
local frame, faults, pcs, bios = 0, 0, {}, 0

local function finish(err)
    local h = io.open(REPORT, "w")
    -- stuck: the last second's frames all ended inside one 16-byte stretch of code other than the vblank wait
    -- (the main loop no longer comes round)
    local lo, hi = math.huge, 0
    for i = math.max(1, #pcs - 59), #pcs do lo = math.min(lo, pcs[i]); hi = math.max(hi, pcs[i]) end
    local stuck = #pcs >= 60 and hi - lo < 16 and not (lo >= VBLANK_WAIT[1] and hi <= VBLANK_WAIT[2])
    h:write(string.format("frames %d\nfaults %d\nstuck %d\nbios %d\nlast_pc %06X\n", frame, faults,
        stuck and 1 or 0, bios, pcs[#pcs] or 0))
    if err then h:write("error " .. tostring(err):gsub("\n", " ") .. "\n") end
    h:close()
    manager.machine:exit()
end

local function step()
    frame = frame + 1
    for _, h in ipairs(HOLD) do
        joy.fields[h[3]]:set_value((frame >= h[1] and frame <= h[2]) and 1 or 0)
    end
    local pc = cpu.state["PC"].value
    pcs[#pcs + 1] = pc
    if pc >= FAULT[1] and pc <= FAULT[2] then faults = faults + 1 end
    if pc >= 0xC00000 then bios = bios + 1 end        -- frames that ended in the BIOS (a reset lands there)
    for _, f in ipairs(SNAPS) do
        if f == frame then manager.machine.video:snapshot() end
    end
    if frame >= FRAMES then finish() end
end

SUB = emu.register_frame_done(function()
    local ok, err = pcall(step)
    if not ok then pcall(finish, err) end
end)
