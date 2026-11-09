# Windows smoke-test checklist

Test the one-click wrapper before publishing a player release. Use a normal user account, a writable game folder and a fresh copy of the exact supported original. Do not run as administrator.

- [ ] Record the SHA-256 of the original and confirm it is the supported file.
- [ ] Put `Domex-Windows10-Patch.exe` beside the original; double-click it.
- [ ] Confirm the new `flush_them_out-win10.exe` is created and the game starts automatically.
- [ ] Confirm the original SHA-256 is unchanged and the patched SHA-256 matches README.
- [ ] Enter a level and test movement, firing, sound and collision.
- [ ] Try the next level; document results instead of assuming they work.
- [ ] Close the game and double-click the patcher again. It should reuse the verified output.
- [ ] Test the patcher from another folder; select the original in the file picker.
- [ ] Cancel the file picker; it should exit without writing anything.
- [ ] Select the installer or an unsupported executable; it should refuse.
- [ ] With a deliberately renamed/disposable unrelated file named `flush_them_out-win10.exe`, verify refusal to overwrite. Do not use an important file for this test.
- [ ] Check an unwritable folder: the tool should explain how to use a writable folder, not request elevation.
- [ ] Remove the patched copy and patcher; the original should remain available.

Record Windows build, GPU, driver, and tested levels in the release notes. The old diagnostic launcher targets the original game and is not part of this public player release.
