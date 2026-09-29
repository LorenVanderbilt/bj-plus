local f=0
local cpu=manager.machine.devices[":maincpu"]
local mem=cpu.spaces["program"]
local function vr(a) mem:write_u16(0x3C0000,a) return mem:read_u16(0x3C0002) end
local B=tonumber(os.getenv("B"))
local cx,cy
emu.register_frame_done(function()
  f=f+1
  if f>=2 then
    mem:write_u32(0x104004,0x00010140) mem:write_u8(0x107009,0x40) mem:write_u32(0x106904,0x3000)
    if not cx then cx,cy=mem:read_u32(0x103058),mem:read_u32(0x103054) end
    mem:write_u8(0x10301E,1) mem:write_u32(0x10301A,cx) mem:write_u32(0x103016,cy)
  end
  if f>=5 and not CALLED and cpu.state["PC"].value==0xE8A8 then CALLED=f
    local sp=cpu.state["SP"].value-4
    mem:write_u32(sp,0xE8A8) cpu.state["SP"].value=sp
    cpu.state["D0"].value=B cpu.state["A6"].value=0x100000 cpu.state["PC"].value=0xD87C
    print("called f"..f)
  end
  if CALLED and f==CALLED+2 then
    local L=mem:read_u16(0x100246)
    print(string.format("blk %04x ring x %d y %d abs x %d y %d", mem:read_u16(0x100244), mem:read_u16(0x10022E), mem:read_u16(0x100222), mem:read_u16(0x100216), mem:read_u16(0x10020A)))
    for r=0,31 do local t="" for c=0,31 do local at=vr((L+c)*64+2*r+1) local tl=vr((L+c)*64+2*r) local k=(at>>4)&15 t=t..(k==0 and ((tl&0xFFF)==0x754 or (tl&0xFFF)==0x755) and "T" or (k==0 and "." or string.format("%x",k))) end print(string.format("r%02d %s",r,t)) end
    manager.machine.video:snapshot()
    manager.machine:exit()
  end
end)
