# Three.js Headless Chromium Compatibility

## The Problem

When using `browser_vision` or `browser_navigate` with Three.js scenes, headless Chromium's WebGL implementation is incomplete. `MeshPhysicalMaterial` and other PBR features crash with:

```
TypeError: Failed to execute 'uniform3fv' on 'WebGL2RenderingContext':
The object must have a callable @@iterator property.
```

## Material Compatibility Matrix

| Material | Headless Safe | Features Lost | Use When |
|----------|--------------|---------------|----------|
| `MeshBasicMaterial` | ✅ Always | No lighting | Wireframes, glows, UI |
| `MeshLambertMaterial` | ✅ Always | No specular | Simple shaded surfaces |
| `MeshPhongMaterial` | ✅ Always | PBR realism | Most 3D models (RECOMMENDED) |
| `MeshStandardMaterial` | ⚠️ Sometimes | Metalness/roughness | Test first |
| `MeshPhysicalMaterial` | ❌ Never | clearcoat, sheen, transmission | Avoid in headless |
| `ShaderMaterial` | ⚠️ Depends | Custom shaders | Test GLSL compatibility |

## Safe Material Pattern

```javascript
// WRONG — crashes headless Chromium
const material = new THREE.MeshPhysicalMaterial({
    color: 0xaa2222,
    roughness: 0.6,
    metalness: 0.1,
    clearcoat: 0.3,        // ← BREAKS HEADLESS
    sheen: 0.2,            // ← BREAKS HEADLESS
    sheenColor: new THREE.Color(0xff4444)
});

// CORRECT — works everywhere
const material = new THREE.MeshPhongMaterial({
    color: 0xaa2222,
    shininess: 60,
    specular: 0x444444
});
```

## Quick Fix Script

If a Three.js scene renders black in `browser_vision`, replace all `MeshPhysicalMaterial` with `MeshPhongMaterial` and remove PBR properties:

```bash
# Replace in HTML/JS files
sed -i '' 's/MeshPhysicalMaterial/MeshPhongMaterial/g' file.html
# Then manually remove: roughness, metalness, clearcoat, clearcoatRoughness, sheen, sheenColor, transmission
```

## Verification

After material swap, check browser console:
```javascript
// Should return "object" and render without errors
typeof THREE
renderer.render(scene, camera)
```

## Related
- `references/macbook-playwright-setup.md` — Playwright version management
