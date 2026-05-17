# visual-regression-testing-webgl-threejs

*Researched: 2026-04-05 02:13 CDT*

# Visual Regression Testing for WebGL/Three.js Applications

## Summary
Practical approaches for automated screenshot-based visual regression testing of 3D anatomy viewers (SOMA). WebGL canvas presents unique challenges vs standard DOM testing.

## Key Findings

### Tool Stack
- **Playwright** is the leading tool for visual regression. Has built-in `expect(page).toHaveScreenshot()` with configurable pixel diff thresholds.
- **pixelmatch** (npm) — lightweight pixel-diff library used by most tools. Can compare two PNG buffers and output diff image.
- **Puppeteer** also viable but Playwright has better WebGL support and cross-browser testing.

### WebGL-Specific Challenges
1. **Non-deterministic rendering**: GPU rendering varies across hardware/drivers. Must use `maxDiffPixelRatio` (e.g., 0.01-0.05) instead of exact pixel match.
2. **Canvas-specific capture**: Use `page.locator('canvas').screenshot()` not full-page screenshots.
3. **Animation timing**: Must wait for rendering to complete. Use `page.waitForTimeout()` or poll for WebGL context readiness.
4. **Anti-aliasing variance**: Different GPUs produce different AA results. Use tolerance thresholds.
5. **Three.js already uses Puppeteer for their own regression tests** (GitHub issue #16941) — validates the approach.

### Practical Implementation for SOMA
```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';
export default defineConfig({
  use: {
    baseURL: 'http://localhost:1420',
  },
  expect: {
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.02, // 2% tolerance for WebGL variance
      animations: 'disabled',
    },
  },
});

// anatomy-visual.spec.ts
import { test, expect } from '@playwright/test';
test('skeletal system renders correctly', async ({ page }) => {
  await page.goto('/anatomy/skeletal');
  await page.waitForSelector('canvas');
  await page.waitForTimeout(2000); // Wait for WebGL render
  const canvas = page.locator('canvas');
  await expect(canvas).toHaveScreenshot('skeletal-system.png');
});
```

### CI Integration
- Run in headless Chrome with `--use-gl=swiftshader` for consistent GPU rendering
- Store baseline screenshots in git LFS or dedicated branch
- Fail CI on >2% pixel diff, generate diff images as artifacts

### Alternatives to Pixel Diff
- **Chromatic** (by Storybook) — cloud-based visual testing, $149/mo
- **Percy** by BrowserStack — automated visual review
- **Reg-suit** — open-source, compares images and comments on PRs
- For SOMA's needs, **pixelmatch + Playwright** is sufficient and free.

## Sources
- https://developer.vonage.com/en/blog/how-to-build-a-visual-regression-test-system-using-playwright
- https://github.com/mrdoob/three.js/issues/16941
- https://css-tricks.com/automated-visual-regression-testing-with-playwright/
- https://www.chromatic.com/blog/how-to-visual-test-ui-using-playwright/


## Sources

- https://developer.vonage.com/en/blog/how-to-build-a-visual-regression-test-system-using-playwright
- https://github.com/mrdoob/three.js/issues/16941
- https://css-tricks.com/automated-visual-regression-testing-with-playwright/
- https://www.chromatic.com/blog/how-to-visual-test-ui-using-playwright/
