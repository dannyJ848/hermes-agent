# cornerstone3d-volume-progressive-loading

*Researched: 2026-04-05 13:46 CDT*

# Cornerstone3D Volume Progressive Loading Architecture

## Key Pattern: Interleaved Decimation with Staged Resolution

Cornerstone3D's volume progressive loader uses a **multi-stage interleave pattern** that SOMA can adapt for WebGPU:

### The Interleave Algorithm
1. **Initial images** — Fetch positions 0, 50%, 100% of the volume (3 slices only)
2. **Quarter decimation 4/3** — Every 4th image starting at offset 3 → positions 3,7,11...
3. **Quarter decimation 4/1** — Every 4th image starting at offset 1 → positions 1,5,9...
4. **Fill remaining 4/2 and 4/0** — Complete the full resolution set
5. **Replace low-res with final** — Backfill positions with full-res data

### Performance Benchmarks (512x512x174 volume, 33MB, simulated 4G)
| Method | First Render | Complete |
|--------|-------------|----------|
| HTJ2K Stream | 2503ms | 8817ms |
| HTJ2K Byte Range | 1002ms | 8813ms |

### Key Architecture Insights for SOMA
1. **Decimation = N/F notation**: Every Nth image at F offset. Simple, predictable, parallelizable.
2. **nearbyFrames**: Each stage can fill adjacent frames from loaded data (interpolation).
3. **RequestType priority queues**: INTERACTION queue for first-visible, BACKGROUND queue for backfill.
4. **Cross-viewport interleaving**: Stages interleave across multiple viewports automatically.
5. **Byte range requests**: Can work against any DICOMweb server supporting HTJ2K — no special server needed.
6. **Replicate-then-replace**: Missing positions are filled with replicated/interpolated data, then replaced with actual data.

### SOMA Integration Plan
- **WebGPU advantage**: SOMA can use compute shaders for the replicate/interpolate step instead of CPU-side TypedArray copying
- **Stage model maps directly**: SOMA's streaming loader can use the same N/F decimation pattern
- **Priority queues**: Map to WebGPU command buffer priorities or separate async fetch queues
- **First render <1s achievable**: Byte range approach hits 1s first render on 4G — SOMA can match or beat this with WebGPU compression

### Source
- https://cornerstonejs.org/docs/concepts/progressive-loading/volumeprogressive/


## Sources

- https://cornerstonejs.org/docs/concepts/progressive-loading/volumeprogressive/
- https://cornerstonejs.org/docs/concepts/progressive-loading/
