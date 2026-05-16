# Sprechwerk Health Score Booster

**Vertical:** sprechwerk  
**Current Health Score:** 53/100  
**Target Score:** 60/100  
**Primary Issue:** No new SEO content for 30+ days

## Overview

This automation dispatches the `goldie-pipeline-v2` skill to generate fresh SEO content for the sprechwerk vertical, boosting the health score by an expected +5 points.

## Components

### 1. dispatch-goldie-pipeline.js
Main dispatcher script that:
- Fetches current health score from PostgreSQL
- Triggers `goldie-pipeline-v2` via openclaw skill-runner
- Logs activity to `nexus_activity_log`
- Validates execution via quality gates

**Usage:**