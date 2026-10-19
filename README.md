# HexCompare 0.1.0

PyQt6 desktop tool for address-accurate comparison of Intel HEX firmware images and positional comparison of arbitrary binary files.

## Run

Requires Python 3.10+.

```powershell
python -m pip install -r requirements.txt
python main.py
```

Select **Intel HEX** or **Binary**, then load both files. The default view shows only differing 16-byte blocks. Disable **Only differing blocks** to show all populated blocks.

Columns: address, File 1 HEX, File 2 HEX, File 1 ASCII, File 2 ASCII. Differing bytes are red, missing bytes are shown as `--`. The summary distinguishes changed, modified, added, removed and identical bytes.

Intel HEX supports record types 00–05, checksums, extended segment and linear addresses, and sparse memory. Unspecified addresses are not implicitly filled with 0xFF.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Version 0.1.0.
