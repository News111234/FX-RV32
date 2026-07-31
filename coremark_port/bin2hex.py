#!/usr/bin/env python3
"""Convert binary file to RISC-V hex format (one 32-bit word per line)."""
import sys

with open(sys.argv[1], 'rb') as f:
    data = f.read()

# Pad to 4-byte boundary
while len(data) % 4 != 0:
    data += b'\x00'

with open(sys.argv[2], 'w') as f:
    for i in range(0, len(data), 4):
        # Little-endian word
        word = data[i] | (data[i+1] << 8) | (data[i+2] << 16) | (data[i+3] << 24)
        f.write(f'{word:08x}\n')

print(f'{len(data)//4} words -> {sys.argv[2]}')
