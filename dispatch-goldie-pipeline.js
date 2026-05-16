#!/usr/bin/env node
'use strict';

/**
 * dispatch-goldie-pipeline.js
 * 
 * Dispatches the goldie-pipeline-v2 Skill for the sprechwerk vertical.
 * Triggered by health-score-booster when SEO content is stale (>30 days).
 * 
 * Usage:
 *   node dispatch-goldie-pipeline.js [--dry-run] [--vertical=sprechwerk]
 * 
 * Requirements:
 *   - Access to openclaw Mac Mini (SSH or MCP)
 *   - goldie-pipeline-v2 skill exists in ~/.openclaw/workspace/skills/
 *   - PostgreSQL access for health-score tracking
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Load config
const CONFIG_PATH = path.join(__dirname, 'goldie-config.json');
const config = fs.existsSync(CONFIG_PATH) 
  ? JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'))
  : { vertical: 'sprechwerk', pipeline: 'goldie-pipeline-v2' };

// Parse CLI args
const args = process.argv.slice(2);
const isDryRun = args.includes('--dry-run');
const vertical = args.find(a => a.startsWith('--vertical='))?.split('=')[1] || config.vertical;

console.log(`[dispatch-goldie-pipeline] Starting for vertical: ${vertical}`);
console.log(`[dispatch-goldie-pipeline] Dry-run: ${isDryRun}`);

/**
 * Execute SSH command to Mac Mini
 */
function sshMacMini(command) {
  const sshCmd = `ssh -o ConnectTimeout=10 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 192.168.0.72 '${command}'`;
  console.log(`[SSH] ${command}`);
  
  if (isDryRun) {
    console.log('[DRY-RUN] Would execute SSH command (skipped)');
    return '';
  }
  
  try {
    return execSync(sshCmd, { encoding: 'utf8', stdio: 'pipe' });
  } catch (error) {
    console.error(`[SSH ERROR] ${error.message}`);
    if (error.stderr) console.error(error.stderr);
    throw error;
  }
}

/**
 * Get current health score from PostgreSQL
 */
function getHealthScore() {
  console.log('[health-score] Fetching current score...');
  
  const query = `
    SELECT score, last_updated 
    FROM health_scores 
    WHERE vertical = '${vertical}' 
    ORDER BY last_updated DESC 
    LIMIT 1
  `;
  
  const psqlCmd = `/opt/homebrew/Cellar/postgresql@17/17.9/bin/psql -d clawdbot_memory -t -c "${query}"`;
  
  try {
    const result = sshMacMini(psqlCmd);
    const match = result.trim().match(/(\d+)\s*\|\s*(.+)/);
    
    if (match) {
      return {
        score: parseInt(match[1], 10),
        lastUpdated: match[2].trim()
      };
    }
  } catch (error) {
    console.warn('[health-score] Could not fetch (table may not exist yet)');
  }
  
  return { score: null, lastUpdated: null };
}

/**
 * Dispatch goldie-pipeline-v2 via skill-runner
 */
function dispatchGoldiePipeline() {
  console.log(`[dispatch] Triggering ${config.pipeline} for ${vertical}...`);
  
  const params = JSON.stringify({
    vertical: vertical,
    contentTypes: config.contentTypes || ['blog', 'service-pages'],
    minWordCount: config.minWordCount || 800,
    targetKeywords: config.targetKeywords || 10,
    qualityThreshold: config.qualityThreshold || 0.75
  });
  
  const skillRunnerCmd = `/opt/homebrew/bin/node ~/.openclaw/workspace/skills/workflow-engine/scripts/skill-runner.js run ${config.pipeline} --params='${params}'`;
  
  try {
    const output = sshMacMini(skillRunnerCmd);
    console.log('[dispatch] Pipeline output:');
    console.log(output);
    
    // Parse output for success indicators
    const success = output.includes('status: completed') || output.includes('SUCCESS');
    return { success, output };
    
  } catch (error) {
    console.error('[dispatch] Pipeline failed');
    return { success: false, error: error.message };
  }
}

/**
 * Log activity to nexus_activity_log
 */
function logActivity(action, result) {
  console.log(`[activity-log] Logging action: ${action}`);
  
  const logEntry = JSON.stringify({
    entity_type: 'vertical',
    entity_id: vertical,
    action: `goldie_dispatch.${action}`,
    result: result.success ? 'success' : 'failed',
    details: JSON.stringify({ 
      pipeline: config.pipeline, 
      output: result.output || result.error 
    })
  });
  
  const insertCmd = `/opt/homebrew/Cellar/postgresql@17/17.9/bin/psql -d clawdbot_memory -c "INSERT INTO nexus_activity_log (entity_type, entity_id, action, details, created_at) VALUES ('vertical', '${vertical}', '${action}', '${logEntry}', NOW())"`;
  
  try {
    sshMacMini(insertCmd);
    console.log('[activity-log] Logged successfully');
  } catch (error) {
    console.warn('[activity-log] Could not log to DB:', error.message);
  }
}

/**
 * Main execution
 */
async function main() {
  console.log('\n=== Goldie Pipeline Dispatch ===\n');
  
  // Step 1: Get baseline health score
  const beforeScore = getHealthScore();
  console.log(`[baseline] Current health score: ${beforeScore.score || 'unknown'}`);
  
  // Step 2: Dispatch pipeline
  const result = dispatchGoldiePipeline();
  
  if (!result.success) {
    console.error('\n[FAILED] Pipeline dispatch unsuccessful');
    logActivity('dispatch_failed', result);
    process.exit(1);
  }
  
  console.log('\n[SUCCESS] Pipeline dispatch completed');
  logActivity('dispatch_success', result);
  
  // Step 3: Wait for score update (optional - score updates may be async)
  console.log('\n[info] Health score will update asynchronously');
  console.log('[info] Run monitor-health-score.js to track progress');
  
  console.log('\n=== Dispatch Complete ===\n');
  process.exit(0);
}

// Run if called directly
if (require.main === module) {
  main().catch(error => {
    console.error('[FATAL]', error);
    process.exit(1);
  });
}

module.exports = { dispatchGoldiePipeline, getHealthScore };