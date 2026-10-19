import tempfile
import unittest
from pathlib import Path
from core import HexFormatError, compare, load_binary, load_intel_hex

def record(address, kind, payload=b""):
    body = bytes([len(payload)]) + address.to_bytes(2, "big") + bytes([kind]) + payload
    return ":" + (body + bytes([-sum(body) & 255])).hex().upper()

class CoreTests(unittest.TestCase):
    def test_sparse(self):
        r = compare({0: 1, 16: 2, 100: 3}, {0: 1, 16: 4, 101: 5})
        self.assertEqual((r.modified, r.removed, r.added, r.identical), (1, 1, 1, 1))
        self.assertEqual(r.blocks, (16, 96))

    def test_extended_linear(self):
        content = "\n".join([record(0, 4, b"\x00\x01"), record(16, 0, b"\xab\xcd"), record(0, 1)])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "a.hex"
            path.write_text(content)
            self.assertEqual(load_intel_hex(path), {0x10010: 0xab, 0x10011: 0xcd})

    def test_checksum(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.hex"
            path.write_text(":00000001FE\n")
            with self.assertRaises(HexFormatError):
                load_intel_hex(path)

    def test_binary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.bin"
            path.write_bytes(b"\x00\xfe")
            self.assertEqual(load_binary(path), {0: 0, 1: 254})

if __name__ == "__main__":
    unittest.main()
