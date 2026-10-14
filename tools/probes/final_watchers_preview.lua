-- Preview (not in the ROM): orange bouncers from Jungle Zone 1 watching the final fight, one behind the balcony's
-- rail and one behind the gold lattice by the floor (the throne hall's left side). Run from the final boss save:
--   ./run.sh -- -state boss_final -autoboot_script tools/probes/final_watchers_preview.lua
-- The hall is one layer of full-height strips (sprites 23-43, x = 16 per strip, tile row r at y 16 * (r - 18)), the
-- floor another (100-120); slots between them are free, so a bouncer there is in front of the hall and behind the
-- floor and the fight. A copy of its section's tile row, one slot later, draws the rail back over its lower half.
-- The bouncer: 2x2 tiles, palette 0x15 (the hall has the enemy's colours there too), in the air / landed frames.
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local AIR = {0x3800, 0x3808, 0x3801, 0x3809}       -- (left column top, bottom; right column top, bottom)
local LANDED = {0x3802, 0x380A, 0x3803, 0x380B}
local PALETTE = 0x15
local HEIGHT, PERIOD, LANDED_FOR = 24, 40, 6        -- the bounce: pixels up, frames a hop, frames squashed
local WATCHERS = {    -- (first slot, x, resting top y, the section's tiles (4 across), their palettes, phase)
    {50, 56, 32, {0x282A, 0x282B, 0x282C, 0x282D}, {0xF1, 0xF0, 0xF0, 0xF0}, 0},           -- balcony rail, row 21
    {60, 48, 144, {0x28A2, 0x28A3, 0x28A4, 0x28A5}, {0xF0, 0xF0, 0xF0, 0xF0}, 20},         -- lattice, row 28
}
local SECTION_X = 32
local ROWS_Y = {[32] = 48, [144] = 160}             -- (the section's row on screen, by the bouncer's resting top)
local n = 0

local function vw(addr, value) mem:write_u16(0x3C0000, addr); mem:write_u16(0x3C0002, value) end
local function scb3(y, height) return (((496 - y) & 0x1FF) << 7) | height end

local function in_hall()
    -- the hall's strips: sprite 25 (x 32) a full-height strip whose row 21 is the rail's first tile
    mem:write_u16(0x3C0000, 25 * 64 + 21 * 2)
    return mem:read_u16(0x3C0002) == 0x282A
end

SUB = emu.register_frame_done(function()
    n = n + 1
    mem:write_u16(0x3C0004, 1)
    local hall = in_hall()
    for _, w in ipairs(WATCHERS) do
        local slot, x, top, tiles, pals, phase = table.unpack(w)
        if not hall then
            for s = slot, slot + 5 do vw(0x8200 + s, 0) end
        else
            local t = (n + phase) % PERIOD
            local frame, up = LANDED, 0
            if t >= LANDED_FOR then
                local u = (t - LANDED_FOR) / (PERIOD - LANDED_FOR)
                frame, up = AIR, math.floor(4 * HEIGHT * u * (1 - u) + 0.5)
            end
            for c = 0, 1 do                                 -- the bouncer: 2 columns of 2 tiles
                local s = slot + c
                vw(s * 64 + 0, frame[c * 2 + 1]); vw(s * 64 + 1, PALETTE << 8)
                vw(s * 64 + 2, frame[c * 2 + 2]); vw(s * 64 + 3, PALETTE << 8)
                vw(0x8000 + s, 0x0FFF)
                vw(0x8200 + s, scb3(top - up, 2) | (c == 1 and 0x40 or 0))
                vw(0x8400 + s, x << 7)
            end
            for c = 0, 3 do                                 -- the section's row again, in front
                local s = slot + 2 + c
                vw(s * 64, tiles[c + 1]); vw(s * 64 + 1, pals[c + 1] << 8)
                vw(0x8000 + s, 0x0FFF)
                vw(0x8200 + s, scb3(ROWS_Y[top], 1) | (c > 0 and 0x40 or 0))
                vw(0x8400 + s, SECTION_X << 7)
            end
        end
    end
end)
