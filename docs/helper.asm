
pushad
sub esp, 32
call getpc
getpc:
pop eax
sub eax, 1888265
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
call 2047954240
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
call 2047954240
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
call 2047954256
add esp, 4
mov eax, dword ptr [esp+4]
mov dword ptr [esp+32], eax
mov eax, dword ptr [esp+8]
mov dword ptr [ebp-20], eax
mov dword ptr [ebp-16], 260
add esp, 32
popad
jmp 2048831972
fail:
mov eax, dword ptr [esp+8]
test eax, eax
jz free_name
push eax
call 2047954256
add esp, 4
free_name:
mov eax, dword ptr [esp+4]
test eax, eax
jz failed_done
push eax
call 2047954256
add esp, 4
failed_done:
add esp, 32
popad
jmp 2048832086
