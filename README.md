# HexCompare 0.1.7

HexCompare is a Python/PyQt6 desktop application for address-aware comparison of Intel HEX firmware images and offset-based comparison of binary files.

## Requirements and startup

Python 3.10+ and the dependencies listed in `requirements.txt` are required.

```powershell
python -m pip install -r requirements.txt
python main.py
```

## Usage

1. Choose **Intel HEX** or **Binary**.
2. Click **Open file 1** and **Open file 2**. A progress bar indicates how much of each file has been read; loading runs in a background thread.
3. Review the summary and highlighted differences.
4. Toggle **Only differing blocks** to show either changed 16-byte blocks (default) or every populated block.
5. Choose a **Diff layout**:
   - **Side by side**: Address | File 1 HEX | File 1 ASCII | File 2 HEX | File 2 ASCII.
   - **Stacked**: Address | File | HEX | ASCII. The two file rows for each block are followed by a blank spacer row.
6. Use **Previous** and **Next** below the table to navigate through results. Up to **200 blocks per page** are rendered to limit UI slowdown for large files.
7. Use **Theme** to switch between **Light** and **Dark**. The selected theme is remembered between launches.

Differing bytes are highlighted in red/pink. Missing bytes appear as `--` in HEX columns. The summary reports changed, modified, added, removed, and identical bytes, plus the number of changed blocks.

## File handling

- **Intel HEX**: record types 00–05, checksum validation, extended segment and linear addresses, sparse address maps, and overlap checks. Unspecified addresses are not automatically filled with `0xFF`.
- **Binary**: bytes are compared by zero-based file offset.

## Performance note

The table displays only one page of blocks at a time, avoiding creation of thousands of row widgets at once. **Comparison and page preparation still run on the GUI thread**, so very large files may still cause a temporary pause. The Windows GUI has not yet been tested for these changes.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Current version: **0.1.7**.
