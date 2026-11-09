# Build and release

## Build the Windows GUI patcher on Linux

Requirements: Python 3, MinGW-w64's i686 compiler and resource compiler.

```bash
sudo apt-get update
sudo apt-get install gcc-mingw-w64-i686 python3
bash build.sh
```

The build uses the checked-in binary difference. It does not download or require the original game. Outputs:

- `release/Domex-Windows10-Patch.exe` — standalone native x86 Windows GUI tool.
- `release/Domex-Windows10-Patch-v1.0.0.zip` — novice-friendly distribution.
- `release/SHA256SUMS.txt` — checksums for the two assets.

No code-signing certificate is included. The executable is unsigned. Do not claim that the release has been signed, Microsoft-approved, or universally antivirus-safe. If a maintainer signs the executable later, re-run `python3 package_release.py` **after signing**, so the ZIP and checksums match the signed binary.

The compiler/linker PE timestamp is disabled and ZIP metadata is fixed. Builds with the same toolchain and resources are intended to be repeatable, but byte-for-byte reproducibility across different compiler versions is not promised.

## Verify the engine difference using your own original game

```bash
python3 tools/verify_patch_data.py /path/to/flush_them_out.exe
```

This reads the original, applies the difference in memory, and checks the exact final hash. It does not write or run a game executable.

For the optional engine-payload regeneration, see `tools/README.md`.

## Publish manually

1. Create an empty public repository and upload the **contents** of the source folder (not just an outer ZIP). Use a descriptive name such as `domex-windows-compatibility-patch`.
2. Keep the `.github` folder so the build workflow is available.
3. Use the maintainer smoke-test checklist when preparing a new version. Keep player instructions in README concise.
4. Create a release with tag **`v1.0.0`**. Paste the text from `RELEASE-NOTES.md`, adjusting any testing statements that have changed.
5. Upload the `.exe`, player ZIP, and `SHA256SUMS.txt` from `release/`.
6. Prefer player download links to those release assets. GitHub's automatic “Source code” ZIP is for developers and is not the compiled player package.

Do not publish the original installer, game executable, patched full game executable, extracted Adobe DLLs/Xtras, or personal diagnostic logs as release assets without the relevant rights/permission.

## GitHub Actions

The included workflow builds on manual dispatch and version tags, then uploads the three release assets as a workflow artifact. It **does not automatically create or publish a release** and needs only read access to repository contents. Download the artifact, run a Windows smoke test, then upload the assets to your release.

The source repository intentionally contains no executable or prebuilt release archive. Generated files in `release/` are ignored by Git; upload them as release assets separately.
