-- Local testing aid (./run.sh with DIFFICULTY set): make a difficulty the chosen one, as if picked in the title
-- menu's OPTIONS (`title-menu`: RAM word 0x10E912 = 0xD100 + level - 1). It only fills it in while none is chosen,
-- so a level picked in OPTIONS, or loaded from the card's save, still wins. Nothing is written until the game's own
-- code runs (the BIOS tests RAM at power-on).
local level = tonumber(os.getenv("HACK_DIFFICULTY") or "")
if not level or level < 1 or level > 8 then return end
local DIFF, DIFF_SET = 0x10E912, 0xD100
local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]
local started = false
emu.register_frame_done(function()
    if not started then
        started = cpu.state["PC"].value < 0x200000        -- in the cartridge, not the BIOS
        if not started then return end
    end
    if (mem:read_u16(DIFF) & 0xFFF8) ~= DIFF_SET then
        mem:write_u16(DIFF, DIFF_SET + level - 1)         -- (the attract cycle's set-up passes it on to the game)
    end
end)
