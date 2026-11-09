/* Domex Windows Compatibility Patch -- community tool, not an official release.
 * MIT license applies to this patcher source; no game ownership is claimed.
 * No downloads, registry changes, injection or elevation. Original stays intact.
 */
#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#define _WIN32_WINNT 0x0601
#include <windows.h>
#include <commdlg.h>
#include <bcrypt.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <wchar.h>

#define APP_TITLE L"Domex Windows Compatibility Patch 1.0"
#define SOURCE_NAME L"flush_them_out.exe"
#define OUTPUT_NAME L"flush_them_out-win10.exe"
#define EXPECTED_SIZE 31989206u
#define PATCH_OFFSET 0x492F60u
#define PATCH_LENGTH 798766u
#define MMAP_SIZE_OFFSET (0x460184u + 32u + 13u * 20u + 4u)
#define NEW_CHUNK_SIZE 772360u
#define RESOURCE_PATCH 101

static const BYTE original_hash[32] = {
  0xf8,0xd1,0x34,0xd5,0xae,0xd3,0xfe,0x2a,0x5e,0x3c,0xa0,0x7a,0xff,0xa7,0x73,0x05,
  0x4a,0x88,0xe6,0x8c,0x8d,0x5b,0xe3,0x16,0x06,0xf2,0x82,0xa0,0x82,0x31,0x73,0xf4
};
static const BYTE patched_hash[32] = {
  0x4c,0x95,0x82,0x46,0x25,0x17,0x97,0xd4,0xd1,0x75,0xcf,0xf2,0xb3,0x99,0x12,0xf8,
  0xe4,0x78,0x91,0x19,0x4d,0x94,0xfd,0x8b,0x18,0x20,0xe1,0x05,0x74,0xa1,0x0a,0xf5
};

static void error_message(const WCHAR *message, DWORD error) {
    WCHAR text[2048];
    if(error) swprintf(text,2048,L"%ls\n\nWindows error code: %lu\n\nNo original game file was modified.",message,error);
    else swprintf(text,2048,L"%ls\n\nNo original game file was modified.",message);
    MessageBoxW(NULL,text,APP_TITLE,MB_OK|MB_ICONERROR);
}
static BOOL sha256(const BYTE *data, ULONG size, BYTE out[32]) {
    BCRYPT_ALG_HANDLE algorithm=NULL;
    BCRYPT_HASH_HANDLE hash=NULL;
    PUCHAR object=NULL;
    DWORD object_size=0,returned=0;
    BOOL ok=FALSE;
    if(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,NULL,0)<0)goto done;
    if(BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,(PUCHAR)&object_size,sizeof(object_size),&returned,0)<0)goto done;
    object=(PUCHAR)HeapAlloc(GetProcessHeap(),0,object_size);
    if(!object)goto done;
    if(BCryptCreateHash(algorithm,&hash,object,object_size,NULL,0,0)<0)goto done;
    if(BCryptHashData(hash,(PUCHAR)data,size,0)<0)goto done;
    if(BCryptFinishHash(hash,out,32,0)<0)goto done;
    ok=TRUE;
done:
    if(hash)BCryptDestroyHash(hash);
    if(object)HeapFree(GetProcessHeap(),0,object);
    if(algorithm)BCryptCloseAlgorithmProvider(algorithm,0);
    return ok;
}
/* Return a buffer only for a regular file of the exact supported size. */
static BYTE *read_game(const WCHAR *path, DWORD *error) {
    HANDLE file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
    BYTE *data=NULL;LARGE_INTEGER size;DWORD got=0;
    *error=0;
    if(file==INVALID_HANDLE_VALUE){*error=GetLastError();return NULL;}
    if(!GetFileSizeEx(file,&size)){*error=GetLastError();goto done;}
    if(size.QuadPart!=EXPECTED_SIZE){*error=ERROR_BAD_LENGTH;goto done;}
    data=(BYTE *)HeapAlloc(GetProcessHeap(),0,EXPECTED_SIZE);
    if(!data){*error=ERROR_NOT_ENOUGH_MEMORY;goto done;}
    if(!ReadFile(file,data,EXPECTED_SIZE,&got,NULL)||got!=EXPECTED_SIZE) {
        *error=GetLastError();if(!*error)*error=ERROR_READ_FAULT;
        HeapFree(GetProcessHeap(),0,data);data=NULL;
    }
done:
    CloseHandle(file);return data;
}
static BOOL regular_file(const WCHAR *path) {
    DWORD attr=GetFileAttributesW(path);
    return attr!=INVALID_FILE_ATTRIBUTES && !(attr&FILE_ATTRIBUTE_DIRECTORY);
}
static BOOL containing_folder(const WCHAR *path,WCHAR folder[MAX_PATH]) {
    if(wcslen(path)>=MAX_PATH)return FALSE;
    wcscpy(folder,path);WCHAR *slash=wcsrchr(folder,L'\\');
    if(!slash)return FALSE;
    *slash=0;return wcslen(folder)<MAX_PATH-48;
}
static BOOL choose_game(HINSTANCE instance,WCHAR path[MAX_PATH]) {
    OPENFILENAMEW dialog;ZeroMemory(&dialog,sizeof(dialog));
    path[0]=0;dialog.lStructSize=sizeof(dialog);dialog.hInstance=instance;
    dialog.lpstrFilter=L"Original Domex game (flush_them_out.exe)\0flush_them_out.exe\0Executable files (*.exe)\0*.exe\0\0";
    dialog.lpstrFile=path;dialog.nMaxFile=MAX_PATH;
    dialog.lpstrTitle=L"Select the ORIGINAL flush_them_out.exe (not the installer)";
    dialog.Flags=OFN_FILEMUSTEXIST|OFN_PATHMUSTEXIST|OFN_NOCHANGEDIR|OFN_DONTADDTORECENT;
    BOOL ok=GetOpenFileNameW(&dialog);
    if(!ok) {
        DWORD e=CommDlgExtendedError();
        if(e)error_message(L"The game selection dialog could not be opened.",e);
    }
    return ok;
}
static BOOL launch_game(const WCHAR *path,const WCHAR *folder) {
    WCHAR command[MAX_PATH+4];STARTUPINFOW startup;PROCESS_INFORMATION process;
    ZeroMemory(&startup,sizeof(startup));startup.cb=sizeof(startup);ZeroMemory(&process,sizeof(process));
    swprintf(command,MAX_PATH+4,L"\"%ls\"",path);
    if(!CreateProcessW(path,command,NULL,NULL,FALSE,0,NULL,folder,&startup,&process)) {
        error_message(L"The patched game is ready, but Windows could not start it.\nTry launching flush_them_out-win10.exe directly from the game folder.",GetLastError());return FALSE;
    }
    CloseHandle(process.hThread);CloseHandle(process.hProcess);return TRUE;
}
int WINAPI wWinMain(HINSTANCE instance,HINSTANCE previous,LPWSTR command,int show) {
    (void)previous;(void)command;(void)show;
    WCHAR source[MAX_PATH],folder[MAX_PATH],output[MAX_PATH],temporary[MAX_PATH];
    DWORD error=0;BYTE hash[32];BYTE *data=NULL;BOOL source_is_patched=FALSE;
    temporary[0]=0;
    DWORD n=GetModuleFileNameW(NULL,source,MAX_PATH);
    if(!n||n>=MAX_PATH||!containing_folder(source,folder)) {
        error_message(L"This folder path is too long. Move the patcher and game to a shorter path, such as C:\\Games\\Domex.",0);return 1;
    }
    swprintf(source,MAX_PATH,L"%ls\\%ls",folder,SOURCE_NAME);
    if(!regular_file(source)) {
        swprintf(source,MAX_PATH,L"%ls\\jeu\\%ls",folder,SOURCE_NAME);
        if(!regular_file(source) && !choose_game(instance,source))return 0;
    }
    if(!containing_folder(source,folder)) {
        error_message(L"The game folder path is too long. Copy the complete game folder to a shorter path, such as C:\\Games\\Domex.",0);return 1;
    }
    data=read_game(source,&error);
    if(!data) {
        if(error==ERROR_BAD_LENGTH)error_message(L"This is not the supported game executable.\nSelect flush_them_out.exe from the installed/extracted game folder, not domex_flush_them_out.exe (the installer).",0);
        else error_message(L"The original game executable could not be read. Make sure the game is closed, then try again.",error);
        return 1;
    }
    if(!sha256(data,EXPECTED_SIZE,hash)) {
        error_message(L"Windows could not calculate the file's SHA-256 checksum.",0);goto fail;
    }
    source_is_patched=memcmp(hash,patched_hash,32)==0;
    if(source_is_patched) {
        HeapFree(GetProcessHeap(),0,data);return launch_game(source,folder)?0:1;
    }
    if(memcmp(hash,original_hash,32)!=0) {
        error_message(L"This version of the game is not supported, or the file has already been modified.\nFor safety, the patch was not applied. Use the unmodified original release listed in README.md.",0);goto fail;
    }
    swprintf(output,MAX_PATH,L"%ls\\%ls",folder,OUTPUT_NAME);
    if(GetFileAttributesW(output)!=INVALID_FILE_ATTRIBUTES) {
        BYTE *existing=read_game(output,&error);BOOL matches=FALSE;
        if(existing) {
            matches=sha256(existing,EXPECTED_SIZE,hash)&&memcmp(hash,patched_hash,32)==0;
            HeapFree(GetProcessHeap(),0,existing);
        }
        if(!matches) {
            error_message(L"A different file named flush_them_out-win10.exe already exists.\nNothing was overwritten. Rename that file, then run this patcher again.",0);goto fail;
        }
        HeapFree(GetProcessHeap(),0,data);return launch_game(output,folder)?0:1;
    }
    HRSRC resource=FindResourceW(instance,MAKEINTRESOURCEW(RESOURCE_PATCH),RT_RCDATA);
    DWORD resource_size=resource?SizeofResource(instance,resource):0;
    HGLOBAL loaded=resource?LoadResource(instance,resource):NULL;
    const BYTE *patch=loaded?(const BYTE *)LockResource(loaded):NULL;
    if(!patch||resource_size!=PATCH_LENGTH) {
        error_message(L"The patch data is missing or damaged. Download a fresh copy of this patcher.",0);goto fail;
    }
    for(DWORD i=0;i<PATCH_LENGTH;i++)data[PATCH_OFFSET+i]^=patch[i];
    data[MMAP_SIZE_OFFSET]=(BYTE)NEW_CHUNK_SIZE;
    data[MMAP_SIZE_OFFSET+1]=(BYTE)(NEW_CHUNK_SIZE>>8);
    data[MMAP_SIZE_OFFSET+2]=(BYTE)(NEW_CHUNK_SIZE>>16);
    data[MMAP_SIZE_OFFSET+3]=(BYTE)(NEW_CHUNK_SIZE>>24);
    if(!sha256(data,EXPECTED_SIZE,hash)||memcmp(hash,patched_hash,32)!=0) {
        error_message(L"The patched file failed its integrity check. No game executable was written.\nDownload a fresh copy of this patcher and try again.",0);goto fail;
    }
    if(!GetTempFileNameW(folder,L"DMP",0,temporary)) {
        error_message(L"The patched game cannot be saved in this folder.\nCopy the COMPLETE game folder to a writable location, such as Documents\\Domex, place this patcher there, and try again.\nDo not run the patcher as administrator.",GetLastError());goto fail;
    }
    HANDLE file=CreateFileW(temporary,GENERIC_WRITE,0,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
    if(file==INVALID_HANDLE_VALUE) {
        error=GetLastError();DeleteFileW(temporary);temporary[0]=0;
        error_message(L"A temporary output file could not be opened.",error);goto fail;
    }
    DWORD written=0;
    BOOL saved=WriteFile(file,data,EXPECTED_SIZE,&written,NULL)&&written==EXPECTED_SIZE;
    if(saved)saved=FlushFileBuffers(file);
    error=saved?0:GetLastError();CloseHandle(file);
    if(!saved) {
        DeleteFileW(temporary);temporary[0]=0;
        error_message(L"The patched game could not be saved. Check free disk space and folder permissions.",error?error:ERROR_WRITE_FAULT);goto fail;
    }
    BYTE *check=read_game(temporary,&error);BOOL verified=FALSE;
    if(check) {
        verified=sha256(check,EXPECTED_SIZE,hash)&&memcmp(hash,patched_hash,32)==0;
        HeapFree(GetProcessHeap(),0,check);
    }
    if(!verified) {
        DeleteFileW(temporary);temporary[0]=0;
        error_message(L"The saved file failed its integrity check. The temporary file was removed.",error);goto fail;
    }
    if(!MoveFileExW(temporary,output,MOVEFILE_WRITE_THROUGH)) {
        error=GetLastError();DeleteFileW(temporary);temporary[0]=0;
        error_message(L"The patched file could not be moved into place. Close any running copies of the game and try again.\nNo existing executable was overwritten.",error);goto fail;
    }
    temporary[0]=0;HeapFree(GetProcessHeap(),0,data);
    return launch_game(output,folder)?0:1;
fail:
    if(temporary[0])DeleteFileW(temporary);
    if(data)HeapFree(GetProcessHeap(),0,data);
    return 1;
}
