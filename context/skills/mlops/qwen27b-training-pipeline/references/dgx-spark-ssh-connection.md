# DGX Spark SSH Connection Pattern

**Date:** May 8, 2026  
**System:** DGX Spark (NVIDIA GB10)

## Connection Details

The DGX Spark uses NVIDIA's Sync system for SSH key management. The config is NOT in the standard `~/.ssh/config` but in a vendor-specific location.

### SSH Config Location
```
~/Library/Application Support/NVIDIA/Sync/config/ssh_config
```

### Contents
```
Host spark-85e8.local
  Hostname spark-85e8.local
  User djg6228
  Port 22
  IdentityFile "~/Library/Application Support/NVIDIA/Sync/config/nvsync.key"
```

### Alternative Address
- Hostname: `spark-85e8.local`
- IP: `10.0.0.171`
- Username: `djg6228` (NOT `danny`, `ubuntu`, `nvidia`, or `root`)
- Key: `nvsync.key` (managed by NVIDIA Sync)

## Verification Commands

```bash
# Check if NVIDIA Sync config exists
cat ~/Library/Application Support/NVIDIA/Sync/config/ssh_config

# Test connection
ssh -i ~/Library/Application Support/NVIDIA/Sync/config/nvsync.key djg6228@spark-85e8.local "echo 'connected'"

# Or use IP
ssh -i ~/Library/Application Support/NVIDIA/Sync/config/nvsync.key djg6228@10.0.0.171 "echo 'connected'"
```

## User Frustration Signal

User said: "omg look through the master doc and prior sessions" — this means the connection details were already documented but I failed to find them. Always check:
1. `~/.ssh/config` (includes directive)
2. `~/Library/Application Support/NVIDIA/Sync/config/ssh_config` (actual DGX config)
3. Prior session memory for "spark", "dgx", "10.0.0.171"

Before asking user for credentials.

## Key Lesson

**Don't ask for SSH details that are already in vendor-managed configs.** The DGX Spark connection is not a standard SSH setup — it's managed by NVIDIA Sync. Check the vendor config first.
