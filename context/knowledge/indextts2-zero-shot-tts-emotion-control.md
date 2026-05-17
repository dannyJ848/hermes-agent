# indextts2-zero-shot-tts-emotion-control

*Researched: 2026-04-05 21:08 CDT*

# IndexTTS2: Zero-Shot TTS with Emotional Disentanglement

**Date:** April 5, 2026
**Source:** https://github.com/index-tts/index-tts (19,821★, Apache 2.0)

## Summary
IndexTTS2 is an industrial-level zero-shot TTS that achieves **disentanglement between emotional expression and speaker identity**. You can independently control voice timbre (from a voice prompt) and emotional style (from a style prompt). It also supports precise duration control via token count specification — critical for audio-visual synchronization.

## Key Innovation
- First AR TTS to fully disentangle emotion from speaker identity
- Dual generation modes: free AR (natural prosody) and duration-specified (precise timing)
- 3.5% WER on English, 1.2% CER
- 19.8K GitHub stars, actively maintained (400 open issues = active community)

## SOMA Relevance
- Bilingual medical narration: can use different reference clips for EN/ES with same "narrator personality"
- Clinical vs. educational modes: emotion control enables calm narration vs. urgent alerts
- AV synchronization: duration control for 3D anatomy walkthrough videos
- Zero-shot cloning means one reference sample per voice

## Comparison
- vs Chatterbox-Turbo (24K★): IndexTTS2 wins on emotion control + duration; Chatterbox wins on speed (350M params) and multilingual
- vs Fish Speech V1.5: IndexTTS2 wins on emotion disentanglement; Fish wins on multilingual (EN/ZH/JP)
- Best use: When you need expressive, controlled TTS for medical education content

## Hermes Skill Created
`mlops/indextts2` — includes installation, usage, SOMA integration patterns, comparison table


## Sources

- https://github.com/index-tts/index-tts
- https://www.siliconflow.com/articles/en/best-open-source-music-generation-models
