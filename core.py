"""Intel HEX and binary address-aware comparison."""
from dataclasses import dataclass
from pathlib import Path

class HexFormatError(ValueError):
    pass

def load_intel_hex(path, progress=None):
    memory = {}
    base = 0
    eof = False
    total = Path(path).stat().st_size
    with open(path, "rb") as stream:
        for number, raw in enumerate(stream, 1):
            line = raw.decode('utf-8-sig').strip()
            if progress:
                progress(min(100, int(stream.tell() * 100 / max(total, 1))))
            if not line:
                continue
            if eof or not line.startswith(":"):
                raise HexFormatError(f"Line {number}: invalid record")
            try:
                record = bytes.fromhex(line[1:])
            except ValueError as exc:
                raise HexFormatError(f"Line {number}: invalid hex") from exc
            if len(record) < 5 or len(record) != record[0] + 5 or sum(record) % 256:
                raise HexFormatError(f"Line {number}: invalid length/checksum")
            count = record[0]
            offset = int.from_bytes(record[1:3], "big")
            kind = record[3]
            data = record[4:-1]
            if kind == 0:
                if offset + count > 65536:
                    raise HexFormatError(f"Line {number}: 64K boundary crossed")
                for i, value in enumerate(data):
                    address = base + offset + i
                    if address > 0xffffffff:
                        raise HexFormatError("Address overflow")
                    if address in memory and memory[address] != value:
                        raise HexFormatError(f"Line {number}: conflicting overlap")
                    memory[address] = value
            elif kind == 1:
                if count or offset:
                    raise HexFormatError("Invalid EOF")
                eof = True
            elif kind in (2, 4):
                if count != 2 or offset:
                    raise HexFormatError("Invalid base record")
                base = int.from_bytes(data, "big") << (4 if kind == 2 else 16)
            elif kind in (3, 5):
                if count != 4 or offset:
                    raise HexFormatError("Invalid start address")
            else:
                raise HexFormatError(f"Unsupported record type {kind}")
    if not eof:
        raise HexFormatError("Missing EOF")
    if progress:
        progress(100)
    return memory

def load_binary(path, progress=None):
    memory = {}
    total = Path(path).stat().st_size
    with open(path, 'rb') as stream:
        offset = 0
        while chunk := stream.read(65536):
            memory.update((offset + i, value) for i, value in enumerate(chunk))
            offset += len(chunk)
            if progress:
                progress(min(100, int(offset * 100 / max(total, 1))))
    if progress:
        progress(100)
    return memory

@dataclass(frozen=True)
class Comparison:
    changed: tuple
    added: int
    removed: int
    modified: int
    identical: int
    blocks: tuple

def compare(left, right):
    addresses = sorted(left.keys() | right.keys())
    changed = tuple(a for a in addresses if left.get(a) != right.get(a))
    return Comparison(
        changed,
        sum(a not in left for a in changed),
        sum(a not in right for a in changed),
        sum(a in left and a in right for a in changed),
        len(addresses) - len(changed),
        tuple(sorted({a // 16 * 16 for a in changed})),
    )
