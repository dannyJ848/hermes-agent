---
name: auto-none-workflow
version: 1.0.0
created: 2026-05-09
auto_generated: true
---

# Auto None Workflow

Auto-generated skill from 20 learnings in the last 24 hours. Primary domain: None. 

## Trigger Conditions

- Working with None
- Need to Hermes expects chromium_headless_shell-1217 but 'playwright install chromium' may install a different build

## Steps

1. **Hermes expects chromium_headless_shell-1217 but 'playwright install chromium' may install a different build**
   - Hermes expects chromium_headless_shell-1217 but 'playwright install chromium' may install a different build. Use 'npx playwright install' to match the version in hermes's playwright dependency.
   - Category: browser, Confidence: 9.00

2. **Headless chromium cannot render MeshPhysicalMaterial (three**
   - Headless chromium cannot render MeshPhysicalMaterial (three.js r128). Use MeshPhongMaterial or MeshLambertMaterial for WebGL compatibility in browser_vision screenshots.
   - Category: browser, Confidence: 8.00

3. **Use patch instead of write_file for surgical material fixes in large HTML files**
   - Use patch instead of write_file for surgical material fixes in large HTML files. Preserves structure and reduces write overhead.
   - Category: code, Confidence: 7.00

4. **Use execute_code with os**
   - Use execute_code with os.listdir + shutil.move for bulk archival. Much faster than individual terminal calls.
   - Category: None, Confidence: 0.95

5. **cat >> file << 'EOF' is reliable for appending multi-line content**
   - cat >> file << 'EOF' is reliable for appending multi-line content. Use 'EOF' (quoted) to prevent variable expansion.
   - Category: None, Confidence: 0.95

6. **Use write_file when patch fails after 2 attempts**
   - Use write_file when patch fails after 2 attempts
   - Category: None, Confidence: 0.90

7. **Use offset/limit for large files, avoid truncation errors**
   - Use offset/limit for large files, avoid truncation errors
   - Category: None, Confidence: 0.90

8. **When patch fails with 'identical strings', the old_string and new_string are the same**
   - When patch fails with 'identical strings', the old_string and new_string are the same. Check before calling.
   - Category: None, Confidence: 0.90

9. **File was modified since last read**
   - File was modified since last read. Always re-read before patching, or use write_file for full replacement.
   - Category: None, Confidence: 0.90

10. **When appending methods to Python files, they must be inside the class, not after if __name__ == '__main__'**
   - When appending methods to Python files, they must be inside the class, not after if __name__ == '__main__'. Use patch with exact context.
   - Category: None, Confidence: 0.90

## Verification

- [ ] Test steps in isolation
- [ ] Confirm trigger conditions match real usage
- [ ] Review and refine if needed
