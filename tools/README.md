# Developer tools

These tools are **not required by players**. Never ask a novice to install Python or run these scripts just to play.

## Verify the checked-in difference

Python standard library only:

```bash
python3 tools/verify_patch_data.py /path/to/original/flush_them_out.exe
```

This requires your own exact supported original. It does not write or execute the game.

## Regenerate the engine fix from the original

Optional dependencies:

```bash
python3 -m pip install pefile keystone-engine zopfli unicorn
python3 tools/generate_patch.py /path/to/original/flush_them_out.exe
python3 tools/test_helper.py
python3 tools/verify_patch_data.py /path/to/original/flush_them_out.exe
bash build.sh
```

Generation extracts the embedded Xtra, adds the helper section, updates relocation metadata, recompresses it to fit the existing file allocation and writes the intermediate patched executable/Xtra to `.generated/`. It then regenerates `resources/patch-data.bin` as an XOR difference. The input original is hash-checked and is not modified.

The intermediate `.generated/` folder contains complete reconstructed third-party material and is ignored by Git. **Do not publish that folder as a release asset.** Only the wrapper, player ZIP and checksums belong in the player release.

`test_helper.py` runs the isolated x86 helper tests using mocked allocator/API functions. Passing them is not a whole-game or native Windows GUI test. A new toolchain/compressor version may produce different bytes; investigate any hash change rather than silently changing the supported hash constants.
