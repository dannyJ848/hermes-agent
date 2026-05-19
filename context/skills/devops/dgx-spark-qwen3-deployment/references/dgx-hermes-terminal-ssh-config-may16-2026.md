# DGX Hermes Terminal SSH Config - May 16 2026

## Problem

After DGX power cycle, SSH to MacBook fails with `Host key verification failed`. The known_hosts file has stale entries for the MacBook IP (10.0.0.125).

## Solution

### Option 1: Disable Host Key Checking (for automated scripts)

```bash
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null macbook 'echo "test"'
```

### Option 2: Update SSH Config

File: `/home/djg6228/.ssh/config`

```
Host macbook
    HostName 10.0.0.125
    User dannygomez
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new
    UserKnownHostsFile /dev/null
```

### Option 3: Remove Stale Key

```bash
ssh-keygen -R 10.0.0.125
ssh-keygen -R macbook
```

## SSH Config for DGX-to-MacBook

```
Host macbook
    HostName 10.0.0.125
    User dannygomez
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new
```

## Key Pitfalls

1. **Host key changes after power cycle**: DGX and MacBook may get new host keys after power cycle, causing verification failures.

2. **Known hosts file corruption**: If `~/.ssh/known_hosts` is corrupted, all SSH connections fail. Use `UserKnownHostsFile=/dev/null` to bypass.

3. **Permission issues**: SSH key must have correct permissions:
   ```bash
   chmod 600 ~/.ssh/id_ed25519
   chmod 644 ~/.ssh/id_ed25519.pub
   chmod 700 ~/.ssh
   ```

4. **Agent forwarding**: For nested SSH (DGX -> MacBook -> another host), enable agent forwarding:
   ```
   Host macbook
       ForwardAgent yes
   ```

## Verification

```bash
# Test SSH connection
ssh macbook 'echo "SSH OK"'

# Test file write
ssh macbook 'echo "from dgx" > /tmp/dgx_test.txt && cat /tmp/dgx_test.txt'

# Test with disabled host key checking
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null macbook 'echo "SSH OK (no verify)"'
```
