"""Isolated x86 emulation of the new helper; not a Windows/game test."""
from pathlib import Path
import struct,json
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1]
p=pefile.PE(str(R/'.generated/Shockwave3D-patched.x32'))
assert p.sections[-1].Misc_VirtualSize==408
code=(R/'.generated/helper.bin').read_bytes()

def run(name,base=0x61b00000,fail_alloc=0,sysdir='C:\\WINDOWS\\SysWOW64',bad_length=False):
 u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(base,0x1d0000);u.mem_write(base,p.get_memory_mapped_image())
 u.mem_map(0x100000,0x20000);u.mem_map(0x50000000,0x200000)
 sp=0x108000;bp=0x10a000;old=0x50000100;heap=0x50010000;api=base+0x1cc000
 data=(name+'\0').encode('utf-16le');u.mem_write(old,data)
 u.mem_write(bp-16,struct.pack('<I',2 if bad_length else len(data)))
 u.mem_write(bp-20,b'\0'*4);u.mem_write(base+0x1810c8,struct.pack('<I',api))
 allocations={old:len(data)*2};freed=[];calls=0;writes=[];stopped=[]
 def read32(a):return struct.unpack('<I',u.mem_read(a,4))[0]
 def return_from(result,extra=0):
  esp=u.reg_read(UC_X86_REG_ESP);ret=read32(esp);u.reg_write(UC_X86_REG_EAX,result);u.reg_write(UC_X86_REG_ESP,esp+4+extra);u.reg_write(UC_X86_REG_EIP,ret)
 def onwrite(uc,access,address,size,value,userdata):
  if 0x50000000<=address<0x50200000:
   assert any(a<=address and address+size<=a+n for a,n in allocations.items()),('heap overflow',hex(address),size,allocations)
   writes.append((address,size))
 def hook(uc,address,size,userdata):
  nonlocal heap,calls
  if address in (base+0xeb1e4,base+0xeb256):stopped.append(address);u.emu_stop()
  elif address==base+0x14d40:
   calls+=1;n=read32(u.reg_read(UC_X86_REG_ESP)+4)
   if calls==fail_alloc:return_from(0);return
   a=heap;heap+=(n+0xff)&~0xff;heap+=0x100;allocations[a]=n;return_from(a)
  elif address==base+0x14d50:
   a=read32(u.reg_read(UC_X86_REG_ESP)+4);assert a in allocations,('invalid free',hex(a));del allocations[a];freed.append(a);return_from(0)
  elif address==api:
   esp=u.reg_read(UC_X86_REG_ESP);dest=read32(esp+4);cap=read32(esp+8);assert cap==260
   if len(sysdir)>=cap:return_from(len(sysdir)+1,8)
   else:u.mem_write(dest,(sysdir+'\0').encode('utf-16le'));return_from(len(sysdir),8)
 u.hook_add(UC_HOOK_CODE,hook);u.hook_add(UC_HOOK_MEM_WRITE,onwrite)
 u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_EBP,bp);u.reg_write(UC_X86_REG_EDI,old);u.reg_write(UC_X86_REG_ESI,0x12345678);u.reg_write(UC_X86_REG_EBX,0)
 # Start at the patched original site to test the detour too.
 u.emu_start(base+0xeb1a1,base+0x1ce000,count=1000000)
 assert stopped and u.reg_read(UC_X86_REG_ESP)==sp and u.reg_read(UC_X86_REG_EBP)==bp
 assert u.reg_read(UC_X86_REG_ESI)==0x12345678 and u.reg_read(UC_X86_REG_EBX)==0
 success=stopped[0]==base+0xeb1e4
 if fail_alloc or bad_length or len(sysdir)>=260:
  assert not success and old not in freed and len(allocations)==1
  return dict(success=False,case=name[:60],alloc_failure=fail_alloc)
 assert success and freed==[old]
 def wstr(a):
  out=bytearray()
  while True:
   c=bytes(u.mem_read(a+len(out),2))
   if c==b'\0\0':return out.decode('utf-16le')
   out.extend(c)
 normalized=wstr(u.reg_read(UC_X86_REG_EDI));path=wstr(read32(bp-20))
 expected=name if name.lower().endswith('.dll') else name+'.dll'
 assert normalized==expected,(normalized,expected)
 absolute=name.startswith('\\') or len(name)>1 and name[1]==':'
 assert path==(expected if absolute else sysdir.rstrip('\\')+'\\'+expected),(path,expected)
 assert len(allocations)==2
 return dict(success=True,case=name[:60],characters=len(name),base=hex(base),path_characters=len(path))

names=['nvldumdx','nvldumdx.dll','NVLDUMDX.DLL','C:\\Windows\\System32\\DriverStore\\FileRepository\\'+('nvidia_driver_package_'*20)+'\\nvldumdx',r'\\server\share\driver.dll','a','pilote_éà','x'*32700]
results=[]
for base in [0x7a100000,0x61b00000,0x24000000]:
 for name in names:results.append(run(name,base))
for fail in [1,2]:results.append(run('nvldumdx',fail_alloc=fail))
results.append(run('nvldumdx',sysdir='x'*260))
results.append(run('nvldumdx',bad_length=True))
(R/'.generated/emulation-tests.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
print('PASS:',len(results),'helper emulation cases. Not a Windows validation.')
