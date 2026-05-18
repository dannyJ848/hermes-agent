# NTFS External SSD on macOS — May 2026

## Problem

DGX Spark GB10 external SSD is NTFS-formatted (8TB). When connected to MacBook for file transfer, macOS cannot write to it natively.

## Symptoms

```bash
# mount -t ntfs fails
mount: exec /Library/Filesystems/ntfs.fs/Contents/Resources/mount_ntfs: No such file or directory

# ntfs-3g via brew fails
brew install ntfs-3g
# → ntfs-3g: Linux is required for this software.
# → libfuse@2: Linux is required for this software.
```

## Root Cause

- macOS removed native NTFS write support in recent versions
- `ntfs-3g` requires Linux (FUSE dependency)
- macOS FUSE implementations (macFUSE) are separate and complex

## Options

| Option | Speed | Data Loss | Complexity |
|--------|-------|-----------|------------|
| Reformat to exFAT | N/A | Yes (all data) | Low |
| Network transfer (rsync) | Slow (2-6h for 337GB) | No | Low |
| Use Linux machine as bridge | Fast | No | Medium |
| macFUSE + ntfs-3g macOS port | Fast | No | High |

## Verified Safe Disconnection

Disconnecting the external SSD from DGX does NOT interrupt benchmarks:
- Benchmarks run from internal `nvme0n1` (`/data/`)
- External SSD is mounted at `/mnt/bigssd` for datasets only
- `df` and `lsblk` confirm separation

## Workaround Used

Network transfer via rsync from MacBook to DGX (slow but works):
```bash
rsync -avP --progress ~/datasets/ djg6228@10.0.0.171:/mnt/bigssd/datasets/
```

## Prevention

Format external SSD as exFAT from the start for cross-platform compatibility:
```bash
# On DGX (Linux)
sudo mkfs.exfat /dev/sda2
# Then mount on both DGX and MacBook
```
