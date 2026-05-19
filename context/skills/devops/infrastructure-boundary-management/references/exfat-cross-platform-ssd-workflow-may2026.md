# exFAT Cross-Platform SSD Workflow — May 2026

## Problem

DGX Spark GB10 external SSD was NTFS-formatted (8TB). When connected to MacBook for file transfer, macOS could not write to it natively. Third-party tools (Mounty) failed to detect the drive.

## Diagnosis

```bash
# SSD detected but mount failed
diskutil mount disk6s2
# → Volume on disk6s2 failed to mount

# Filesystem verification revealed corruption
fsck_msdos -n /dev/rdisk6s2
# → Invalid BS_jmpBoot in boot block: 000000
# → File system check exit code is 201
```

Root cause: NTFS filesystem had boot block corruption, preventing any mount (read or write).

## Resolution: Reformat to exFAT

```bash
# Erase and reformat entire disk to exFAT
diskutil eraseDisk exFAT SSD8TB disk6

# Result:
# Volume name      : SSD8TB
# Volume size      : 8001352105984 bytes (~7.3TB usable)
# Mounted at       : /Volumes/SSD8TB
```

## Cross-Platform Compatibility Matrix

| Format | DGX (Ubuntu) | MacBook | Recommendation |
|--------|-------------|---------|----------------|
| NTFS | ✅ Native read/write | ❌ Read-only (no native write) | DGX-only storage |
| exFAT | ✅ Native read/write | ✅ Native read/write | **Best for cross-platform** |
| APFS | ❌ Not supported | ✅ Native | Mac-only |

## Dataset Transfer

```bash
# From MacBook to exFAT SSD
rsync -avh --progress ~/datasets/ /Volumes/SSD8TB/datasets/

# From exFAT SSD to DGX (when reconnected)
rsync -avh --progress /mnt/bigssd/datasets/ /data/datasets/
```

## Key Lessons

1. **Mounty and third-party NTFS tools are unreliable** — When NTFS has filesystem errors, these tools silently fail. Native macOS tools (`diskutil`) give actual error messages.

2. **Always verify filesystem health before troubleshooting mount issues:**
   ```bash
   diskutil verifyVolume disk6s2
   ```

3. **exFAT is the only format that works seamlessly on both macOS and Ubuntu** without third-party drivers.

4. **When disk is full on MacBook**, Hermes `write_file` and `terminal` tools fail with "No space left on device". Write scripts directly on remote host via SSH instead:
   ```bash
   ssh djg6228@10.0.0.171 "printf '%s\n' '#!/bin/bash' 'cd /data/...' 'command' > /tmp/script.sh"
   ```

## Related

- `references/ntfs-macbook-external-ssd-may2026.md` — Earlier attempt with network transfer workaround
