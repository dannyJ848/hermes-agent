# System Status Check Skill

## Purpose
Provide a comprehensive subsystem status bundle when the user asks about any subsystem's status, eliminating the need for sequential per-subsystem queries.

## Trigger
User asks about the status, state, health, or condition of any subsystem (e.g., cerebrum, honcho, SOMA, or any registered subsystem).

## Instructions
1. Check the status of ALL registered subsystems, not just the one asked about.
2. Provide a detailed response for the specifically requested subsystem.
3. Append a bundled status summary for all other registered subsystems in the same response, formatted as:
   - **[Subsystem Name]**: [status indicator] - [one-line summary]
4. Status indicators should use: ✅ Operational, ⚠️ Degraded, ❌ Down, 🔧 Maintenance

## Registered Subsystems
- cerebrum
- honcho
- SOMA
- (Add new subsystems here as they are registered)

## Example Output Format
```
**cerebrum** (requested):
[Detailed status response here]

---
**Other Subsystems:**
- **honcho**: ✅ Operational - No issues detected
- **SOMA**: ✅ Operational - Processing normally
```

## Notes
- This skill collapses N-turn diagnostic sessions into a single turn.
- Maintains context efficiency while providing comprehensive visibility.
