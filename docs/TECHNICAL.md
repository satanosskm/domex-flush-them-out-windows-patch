# Technical overview

## Observed failure

The original executable is a 32-bit Adobe Director projector. Its bundled runtime identifies as Director 11.5.9r629. The game includes Shockwave 3D levels and a compressed `Shockwave 3D Asset.x32`.

A diagnostic run on the test user's Windows 10 system recorded an unhandled access violation at `IML32.dll + 0x9F1F`, in an internal memory-release routine. Stack address candidates included `Shockwave3D + 0xEB260`, the return address immediately after a release call in the driver-information routine at `+0xEAF9B`.

Static analysis found that routine constructing a driver path in a fixed 260-WCHAR allocation using unbounded concatenation. It also appended `.dll` to the original registry buffer and prefixed the system directory even when a driver string was already an absolute path. These operations are unsafe for sufficiently long modern driver paths.

The evidence was consistent with upstream heap corruption, not necessarily a defect in the IML memory manager. The diagnostic did not trace the first corrupting write. After changing the path construction, the user reported that the game could start and enter a level.

## Engine change

- Original `Shockwave3D` preferred base: `0x7A100000`.
- Six bytes at RVA `0xEB1A1` are replaced with a relative jump and NOP.
- A 408-byte position-independent helper is added in an RX `.dfix` section at RVA `0x1CD000`.
- The overwritten instruction's HIGHLOW relocation at `0xEB1A3` becomes ABSOLUTE (ignored). No new imports or absolute-address relocations are required.
- The helper bounds the source scan using the registry byte count, allocates adequate name/path buffers, preserves absolute paths, avoids duplicate `.dll` extensions, and cleans up on failure.
- Allocation/free wrappers from the same Xtra are reused. IML's release logic remains active; the patch does not merely suppress the access violation.

The replacement Xtra is DEFLATE/zlib compressed with Zopfli. Better compression keeps it within the original file allocation, so the projector's other content offsets and total file size remain unchanged. The Xtra wrapper lengths and its mmap entry size are updated. Game data, levels, controls, other Xtras, and system DLLs are not changed.

## One-click wrapper

The GUI executable embeds an XOR difference for the original file region `[0x492F60, 0x492F60 + 798766)`. It applies that difference and changes the little-endian size at `0x460184 + 32 + 13*20 + 4` to 772360.

The wrapper:
1. Locates the original executable beside itself or in a `jeu` subdirectory, otherwise opens a file picker.
2. Requires the exact original file size and SHA-256.
3. Constructs and hash-checks the result in memory.
4. Writes a temporary file in the same folder, checks it again, and moves it to a new output name **without overwrite permission**.
5. Starts the new executable with the game folder as its working directory.

If the expected patched output already exists and matches its SHA-256, it is simply launched. An unknown output file is never overwritten. The original file is only opened for reading. The patcher runs `asInvoker` and does not change the registry, app-compatibility flags, DEP, GPU settings, or security settings.

## Testing and limits

The helper previously passed 28 Unicorn x86 emulation cases: relative and absolute paths, long names, UNC paths, non-ASCII characters, an existing extension, three load bases, allocation failures, and error paths. These are isolated tests with mocked engine allocators and a mocked Windows API; they do not validate the whole engine.

`tools/verify_patch_data.py` independently checks the shipped binary difference against a user-supplied original executable. It does not need to execute the game. The release PE's embedded resource is also checked during development against that difference.

The hash of the output is identical to the earlier user-tested experimental patch; only its filename differs. The patcher has also passed seven automated Wine runtime cases. The game has not been fully played through. No general Windows 11 compatibility claim is made.

## Evidence included

- `helper.asm`: the replacement helper source.
- `patch-manifest.json`: earlier engine-patch metadata.
- `helper-emulation-results.json`: saved isolated test results, not a whole-game certification.
- `tools/generate_patch.py`: original-Xtra extraction, helper assembly and payload generation.

Original binaries, runtime DLLs, private diagnostics, usernames, and process-memory dumps are intentionally not included.
