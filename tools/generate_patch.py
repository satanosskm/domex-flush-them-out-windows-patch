"""Experimental targeted Domex patch. Requires pefile, keystone-engine, zopfli.
Rebuilds the embedded Shockwave3D Xtra, not IML's memory manager.
Inputs and outputs are hash-checked. No original file is overwritten.
"""
from pathlib import Path
import struct, hashlib, zlib, json
import pefile
from keystone import Ks, KS_ARCH_X86, KS_MODE_32

import argparse
parser=argparse.ArgumentParser(description='Regenerate the Domex engine fix from your own supported original executable.')
parser.add_argument('original',type=Path)
args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=args.original
EXPECTED='f8d134d5aed3fe2a5e3ca07affa773054a88e68c8d5be31606f282a0823173f4'
b=bytearray(ORIGINAL.read_bytes())
assert hashlib.sha256(b).hexdigest()==EXPECTED
mmap_entry=0x460184+32+13*20
tag,size,off=struct.unpack_from('<4sII',b,mmap_entry)
assert tag==b'eliF' and off==0x492f60
old_envelope=bytes(b[off:off+size])
assert old_envelope[:4]==b'RIFF' and old_envelope[8:16]==b'XtraFILE'
xtra=bytearray(zlib.decompress(old_envelope[48:]))
p=pefile.PE(data=xtra)
base=p.OPTIONAL_HEADER.ImageBase
newrva=0x1cd000
newva=base+newrva
site=0xeb1a1
assert bytes(xtra[p.get_offset_from_rva(site):p.get_offset_from_rva(site)+6])==bytes.fromhex('8b35a011287a')
# Entry through a JMP, with EBP retaining the original routine's frame.
# pushad preserves the original registers; the saved EDI is replaced only
# after both allocations have succeeded. No absolute addresses in new code.
asm=f'''
pushad
sub esp, 32
call getpc
getpc:
pop eax
sub eax, {newrva+9}
mov dword ptr [esp+16], eax
mov dword ptr [esp], edi
xor eax, eax
mov dword ptr [esp+4], eax
mov dword ptr [esp+8], eax
mov ecx, dword ptr [ebp-16]
shr ecx, 1
cmp ecx, 32768
jbe bound_ok
mov ecx, 32768
bound_ok:
test ecx, ecx
jz fail
scan:
cmp word ptr [edi+eax*2], 0
je scanned
inc eax
cmp eax, ecx
jb scan
jmp fail
scanned:
test eax, eax
jz fail
mov dword ptr [esp+12], eax
lea eax, [eax*2+10]
push eax
call {base+0x14d40}
add esp, 4
test eax, eax
jz fail
mov dword ptr [esp+4], eax
mov edi, eax
mov esi, dword ptr [esp]
mov ecx, dword ptr [esp+12]
cld
rep movsw
mov word ptr [edi], 0
cmp dword ptr [esp+12], 4
jb add_ext
cmp word ptr [edi-8], 46
jne add_ext
movzx eax, word ptr [edi-6]
or eax, 32
cmp eax, 100
jne add_ext
movzx eax, word ptr [edi-4]
or eax, 32
cmp eax, 108
jne add_ext
movzx eax, word ptr [edi-2]
or eax, 32
cmp eax, 108
je ext_done
add_ext:
mov dword ptr [edi], 0x0064002e
mov dword ptr [edi+4], 0x006c006c
mov word ptr [edi+8], 0
add dword ptr [esp+12], 4
ext_done:
mov eax, dword ptr [esp+12]
lea eax, [eax*2+524]
push eax
call {base+0x14d40}
add esp, 4
test eax, eax
jz fail
mov dword ptr [esp+8], eax
mov esi, dword ptr [esp+4]
cmp word ptr [esi], 92
je absolute_path
cmp word ptr [esi+2], 58
je absolute_path
push 260
push eax
mov edx, dword ptr [esp+24]
call dword ptr [edx+0x1810c8]
test eax, eax
jz fail
cmp eax, 260
jae fail
mov edi, dword ptr [esp+8]
lea edi, [edi+eax*2]
cmp word ptr [edi-2], 92
je copy_name
mov word ptr [edi], 92
add edi, 2
jmp copy_name
absolute_path:
mov edi, dword ptr [esp+8]
copy_name:
mov esi, dword ptr [esp+4]
mov ecx, dword ptr [esp+12]
inc ecx
rep movsw
push dword ptr [esp]
call {base+0x14d50}
add esp, 4
mov eax, dword ptr [esp+4]
mov dword ptr [esp+32], eax
mov eax, dword ptr [esp+8]
mov dword ptr [ebp-20], eax
mov dword ptr [ebp-16], 260
add esp, 32
popad
jmp {base+0xeb1e4}
fail:
mov eax, dword ptr [esp+8]
test eax, eax
jz free_name
push eax
call {base+0x14d50}
add esp, 4
free_name:
mov eax, dword ptr [esp+4]
test eax, eax
jz failed_done
push eax
call {base+0x14d50}
add esp, 4
failed_done:
add esp, 32
popad
jmp {base+0xeb256}
'''
ks=Ks(KS_ARCH_X86,KS_MODE_32)
code=bytes(ks.asm(asm,addr=newva)[0])
assert len(code)<4096
# Remove the HIGHLOW relocation of the overwritten mov operand. The detour
# uses relative addressing; all remaining old code/relocations stay intact.
removed=[]
for block in p.DIRECTORY_ENTRY_BASERELOC:
 for r in block.entries:
  if site <= r.rva < site+6 and r.type:
   assert r.type==3
   struct.pack_into('<H',xtra,r.struct.get_file_offset(),r.rva&0xfff)
   removed.append(r.rva)
assert removed==[site+2]
s=pefile.SectionStructure(p.__IMAGE_SECTION_HEADER_format__)
s.__unpack__(b'\0'*40)
s.set_file_offset(p.sections[-1].get_file_offset()+40)
s.Name=b'.dfix\0\0\0';s.Misc_VirtualSize=len(code);s.VirtualAddress=newrva
s.SizeOfRawData=4096;s.PointerToRawData=len(xtra);s.Characteristics=0x60000020
assert len(xtra)%4096==0 and s.get_file_offset()+40<p.OPTIONAL_HEADER.SizeOfHeaders
xtra[s.get_file_offset():s.get_file_offset()+40]=s.__pack__()
struct.pack_into('<H',xtra,p.FILE_HEADER.get_field_absolute_offset('NumberOfSections'),p.FILE_HEADER.NumberOfSections+1)
struct.pack_into('<I',xtra,p.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfImage'),newrva+4096)
struct.pack_into('<I',xtra,p.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfCode'),p.OPTIONAL_HEADER.SizeOfCode+4096)
struct.pack_into('<I',xtra,p.OPTIONAL_HEADER.get_field_absolute_offset('CheckSum'),0)
detour=bytes(ks.asm(f'jmp {newva}',addr=base+site)[0])+b'\x90'
xtra[p.get_offset_from_rva(site):p.get_offset_from_rva(site)+6]=detour
xtra.extend(code+b'\0'*(4096-len(code)))
patched_pe=pefile.PE(data=xtra)
assert patched_pe.sections[-1].Name==b'.dfix\0\0\0'
assert all(not(site<=r.rva<site+6) or r.type==0 for block in patched_pe.DIRECTORY_ENTRY_BASERELOC for r in block.entries)
output=ROOT/'.generated';output.mkdir(exist_ok=True)
(output/'Shockwave3D-patched.x32').write_bytes(xtra)
(output/'helper.bin').write_bytes(code)
(output/'helper.asm').write_text(asm)
# Use tighter DEFLATE compression to keep all existing EXE offsets intact.
compressed=zlib.compress(xtra,9)
print('helper size',len(code),'old compressed',size-48,'new zlib',len(compressed))
if len(compressed)>size-48:
 import zopfli.zlib
 compressed=zopfli.zlib.compress(bytes(xtra),numiterations=15)
 print('new zopfli',len(compressed))
header=bytearray(old_envelope[:48])
struct.pack_into('>I',header,4,40+len(compressed))
struct.pack_into('>I',header,16,28+len(compressed))
struct.pack_into('>I',header,32,len(xtra))
struct.pack_into('>I',header,40,len(compressed))
envelope=header+compressed
if len(envelope)<=size:
 b[off:off+size]=envelope+b'\0'*(size-len(envelope))
 struct.pack_into('<I',b,mmap_entry+4,len(envelope))
else:
 raise RuntimeError('Compressed block no longer fits; do not emit an unvalidated container rebuild')
assert len(b)==ORIGINAL.stat().st_size
# Round-trip the container and rebuilt PE.
newsize,newoff=struct.unpack_from('<II',b,mmap_entry+4)
assert newoff==off
assert zlib.decompress(b[off+48:off+newsize])==bytes(xtra)
(output/'flush_them_out.exe').write_bytes(b)
meta=dict(original_sha256=EXPECTED,patched_sha256=hashlib.sha256(b).hexdigest(),xtra_sha256=hashlib.sha256(xtra).hexdigest(),helper_rva=newrva,helper_size=len(code),site_rva=site,removed_relocation_rvas=removed,original_chunk_size=size,patched_chunk_size=len(envelope),original_exe_size=len(b),method='new PIC helper section; existing EXE offsets preserved')
(output/'patch-manifest.json').write_text(json.dumps(meta,indent=2))
print(json.dumps(meta,indent=2))

# The public wrapper embeds a difference, never the complete reconstructed Xtra.
original_bytes=ORIGINAL.read_bytes()
padded=bytes(envelope)+b'\0'*(size-len(envelope))
delta=bytes(a^c for a,c in zip(original_bytes[off:off+size],padded))
(ROOT/'resources/patch-data.bin').write_bytes(delta)
print('Updated resources/patch-data.bin. Verify and rebuild the GUI before release.')
