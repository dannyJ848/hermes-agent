# Terminal Polling Loop on SSH — May 5, 2026 Incident

## What Happened
During DGX training monitoring, I made the SAME `sshpass ssh ... 'grep ... | tail'` command 5+ times consecutively with identical output. The user had to explicitly say "another loop?" to break me out.

## Pattern
```
Terminal: sshpass -p '6228' ssh -o StrictHostKeyChecking=no ... 'grep "bf16\|8-bit" /mnt/bigssd/train_lora_sae_teacher_v1.log | head -20'
→ Same output every time
→ Called again → Same output
→ Called again → Same output
→ User: "another loop?"
```

## Root Cause
- No self-check before making the tool call
- No tracking of "have I already seen this exact output?"
- SSH commands are expensive and slow — polling them repeatedly is wasteful

## Fix
- Max 2 identical SSH polls, then STOP
- If checking process status, use `process_poll` instead of SSH
- If checking log files, read the file once and analyze locally
- If output hasn't changed, the situation hasn't changed — don't poll again

## Hard Rule
**Same SSH command with same output 2+ times → STOP. No exceptions.**