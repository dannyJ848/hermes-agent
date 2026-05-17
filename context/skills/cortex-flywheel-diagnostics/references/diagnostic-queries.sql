-- Cortex Flywheel Diagnostic Queries
-- Run these against cerebrum_memory.db to assess flywheel health

-- 1. Injection Effectiveness: what % of tips have ever been accessed?
SELECT 
  COUNT(CASE WHEN access_count > 0 THEN 1 END) * 100.0 / COUNT(*) as hit_rate,
  COUNT(*) as total_tips
FROM distilled_tips;

-- 2. Elo Distribution by tier
SELECT 
  CASE 
    WHEN elo < 1000 THEN 'garbage'
    WHEN elo < 1200 THEN 'bad'
    WHEN elo < 1400 THEN 'weak'
    WHEN elo < 1600 THEN 'ok'
    WHEN elo < 1800 THEN 'good'
    ELSE 'strong'
  END as tier,
  COUNT(*) as count
FROM distilled_tips
GROUP BY tier;

-- 3. Tip Survival tracking
SELECT 
  AVG(survival_rate) as avg_survival,
  COUNT(CASE WHEN opportunities >= 100 AND survival_rate < 0.3 THEN 1 END) as weak_tips
FROM tip_survival;

-- 4. Adversarial validation coverage
SELECT 
  COUNT(*) as tested,
  (SELECT COUNT(*) FROM distilled_tips) as total,
  COUNT(*) * 100.0 / (SELECT COUNT(*) FROM distilled_tips) as coverage_pct
FROM tip_adversarial;

-- 5. Prompt fragment diversity
SELECT fragment_type, COUNT(*) as count, AVG(elo) as avg_elo
FROM prompt_fragments
GROUP BY fragment_type;

-- 6. Enhancement cycle history
SELECT cycle_name, duration_minutes, modules_added, tips_extracted, notes
FROM enhancement_effectiveness
ORDER BY start_time DESC;

-- 7. Error pattern frequency
SELECT pattern_name, occurrence_count, trigger_tool
FROM error_patterns_predictive
ORDER BY occurrence_count DESC;

-- 8. Auto-skill pipeline status
SELECT status, COUNT(*) as count
FROM auto_skill_pipeline
GROUP BY status;
