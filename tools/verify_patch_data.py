"""Verify the public XOR difference without writing or executing any game file."""
from pathlib import Path
import argparse
import hashlib
import struct

EXPECTED_SIZE = 31989206
ORIGINAL_HASH = 'f8d134d5aed3fe2a5e3ca07affa773054a88e68c8d5be31606f282a0823173f4'
PATCHED_HASH = '4c958246251797d4d175cff2b39912f8e47891194d94fd8b1820e10574a10af5'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('original', type=Path, help='your own original flush_them_out.exe')
args = parser.parse_args()
original = args.original.read_bytes()
if len(original) != EXPECTED_SIZE or hashlib.sha256(original).hexdigest() != ORIGINAL_HASH:
    parser.error('Not the exact supported original executable. No files were changed.')
root = Path(__file__).resolve().parents[1]
delta = (root / 'resources/patch-data.bin').read_bytes()
if len(delta) != 798766:
    parser.error('Invalid patch-data length.')
result = bytearray(original)
offset = 0x492F60
result[offset:offset+len(delta)] = bytes(a ^ b for a, b in zip(original[offset:offset+len(delta)], delta))
struct.pack_into('<I', result, 0x460184 + 32 + 13*20 + 4, 772360)
actual = hashlib.sha256(result).hexdigest()
if actual != PATCHED_HASH:
    parser.error(f'Patched hash mismatch: {actual}')
print(f'PASS: {len(result):,} bytes; SHA-256 {actual}')
print('The difference reproduces the exact earlier user-tested patch. No files were written or executed.')
