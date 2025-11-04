# Mix Optimization System - Complete Guide

## Overview

This system creates **3 optimized base electrolyte mixes** using RAG-powered research and batch gradient descent optimization:

1. **Sleep Mix** - Optimized for sleep onset, maintenance, and quality
2. **Active Mix** - Optimized for exercise performance, recovery, and hydration
3. **Daily Mix** - Optimized for general wellness and maintenance

Each mix is trained on batches of diverse user profiles (12+ per iteration) to find the ONE best formulation that works well across a broad population.

---

## System Architecture

### Key Components

```
formulation_engines/
├── sleep_mix_optimizer.py      # Sleep mix formulation engine
├── active_mix_optimizer.py     # Active mix formulation engine
├── daily_mix_optimizer.py      # Daily mix formulation engine
├── batch_test_generator.py     # Generates diverse test case batches
├── mix_optimization_loop.py    # SGD-style training loop
├── parallel_evaluator.py       # RAG-powered evaluation (8+ queries)
├── reasoning_reflector.py      # Meta-reasoning & knowledge gap detection
└── targeted_research_downloader.py  # Downloads new research papers

Root directory:
├── run_mix_optimization.py     # Main entry point
├── mix_research_queries.json   # Research queries for each use case
├── sleep_mix_final.json        # Output: optimized sleep formulation
├── active_mix_final.json       # Output: optimized active formulation
└── daily_mix_final.json        # Output: optimized daily formulation
```

### How It Works (SGD-Style Training)

```
1. Initialize optimizer with default formulation
   ↓
2. Generate batch of 12+ diverse test cases
   ↓
3. Evaluate formulation on entire batch using RAG
   ↓
4. Calculate average score across batch
   ↓
5. Reflect on evaluations → identify knowledge gaps
   ↓
6. Download new research papers to fill gaps
   ↓
7. Calculate averaged gradients (adjustments) across batch
   ↓
8. Apply adjustments to formulation (learning rate 0.3)
   ↓
9. Repeat until convergence or max iterations
   ↓
10. Save best formulation + training history
```

---

## Usage

### Quick Start - Train Single Mix

```bash
cd /home/jschu/projects/Agentic.RAG
source venv/bin/activate

# Train sleep mix
python3 run_mix_optimization.py --use_case sleep --iterations 20

# Train active mix
python3 run_mix_optimization.py --use_case active --iterations 20

# Train daily mix
python3 run_mix_optimization.py --use_case daily --iterations 20
```

### Train All Three Mixes

```bash
python3 run_mix_optimization.py --all --iterations 15
```

### Advanced Options

```bash
python3 run_mix_optimization.py \
  --use_case sleep \
  --iterations 25 \
  --batch_size 15 \
  --learning_rate 0.25
```

**Parameters:**
- `--use_case`: Which mix to train (`sleep`, `active`, `daily`)
- `--all`: Train all three mixes sequentially
- `--iterations`: Max number of training iterations (default: 20)
- `--batch_size`: Test cases per batch (default: 12)
- `--learning_rate`: How aggressively to apply adjustments (default: 0.3)

---

## Training Process Details

### Batch Test Generation

Each iteration generates a fresh batch of diverse test cases:

**Sleep Batch (12 cases):**
- Age: Stratified 18-30, 31-50, 51-70, 70+ (25% each)
- Sex: 50/50 male/female
- Sleep issues: Varied combinations (onset, maintenance, early waking, restless)
- Current intake: Random realistic ranges
- Medications: Age-appropriate (diuretics for 50+)

**Active Batch (12 cases):**
- Age: Skewed younger (50% 18-30, 33% 31-50, 17% 51+)
- Activity: High intensity, endurance, strength, CrossFit, running, cycling
- Training: 4-12 hours/week
- Sweat rate: Moderate, high, very high
- Performance goals: Endurance, strength, recovery

**Daily Batch (12 cases):**
- Age: Even distribution across all age groups
- Activity: Skewed toward sedentary/moderate
- Health goals: General wellness, energy, stress, cardiovascular, bone health
- Diet quality: Poor, average, good

### Evaluation Process

For each test case in batch:
1. Generate recommendation (same formulation for all)
2. Run 8+ parallel RAG queries:
   - 4 mineral-specific queries (Mg, Ca, K, Na)
   - 2 interaction queries (Mg:Ca ratio, K:Na balance)
   - 1 demographic query (age/sex specific)
   - 1 condition query (sleep/performance/wellness specific)
3. Grade each mineral (0-100) with feedback
4. Calculate overall score

### Gradient Calculation

Adjustments averaged across batch:
- Parse suggestions from each evaluation
- Extract dose changes (increase/decrease)
- Average across all 12+ cases
- Apply learning rate (default 0.3)
- Cap at safety limits

Example:
```
Batch of 12 evaluations:
  Case 1: Mg +20mg (score 85)
  Case 2: Mg +15mg (score 82)
  Case 3: Mg +5mg  (score 91)
  ...
  Case 12: Mg +10mg (score 88)

Averaged: Mg +12.5mg
With learning rate 0.3: Mg +3.75mg (rounded to +4mg)
```

### Convergence Criteria

Training stops when:
1. No improvement for 5 consecutive iterations, OR
2. Adjustments < 1mg for all minerals, OR
3. Max iterations reached

---

## Output Files

### Formulation Files (*_mix_final.json)

Example `sleep_mix_final.json`:
```json
{
  "version": "1.2",
  "use_case": "sleep",
  "last_updated": "2025-10-29",
  "description": "Optimized for sleep onset, maintenance, and quality",
  
  "formulation": {
    "magnesium": 425,
    "calcium": 210,
    "potassium": 265,
    "sodium": 140
  },
  
  "forms": {
    "magnesium": "glycinate",
    "calcium": "citrate",
    "potassium": "citrate",
    "sodium": "citrate"
  },
  
  "ratios": {
    "mg_ca": 2.02,
    "k_na": 1.89
  },
  
  "training_history": {
    "iterations": 18,
    "best_score": 87.3,
    "avg_score": 85.1
  },
  
  "research_support": [
    "PMC9941068: Magnesium glycinate 400mg improves sleep onset latency",
    "PMC9331058: Mg:Ca 2:1 ratio optimizes GABA production"
  ]
}
```

### Training History Files (*_mix_training_history.json)

Tracks metrics over iterations:
```json
{
  "iterations": [1, 2, 3, ...],
  "avg_scores": [78.2, 81.5, 83.1, ...],
  "best_scores": [78.2, 81.5, 83.1, ...],
  "formulations": [
    {"magnesium": 400, "calcium": 200, ...},
    {"magnesium": 410, "calcium": 205, ...},
    ...
  ]
}
```

---

## Key Differences from Old System

### Old: `sleep_support_engine.py` (Personalization)
- Creates DIFFERENT mixes for EACH person
- Uses complex rules and multipliers
- Adjusts for age, sex, weight, conditions
- Outputs personalized formulations

### New: `*_mix_optimizer.py` (Single Optimal Mix)
- Creates ONE mix for each use case
- Optimizes across diverse population
- Batch training like ML models
- Outputs single best formulation

**Why Both?**
- Short term: Use single optimized mixes (simpler, faster to market)
- Long term: Add personalization layer on top of base mixes

---

## Research Integration

### Initial Research Bootstrap

Uses `mix_research_queries.json` to pre-populate knowledge base:
```json
{
  "sleep": {
    "semantic_queries": [
      "magnesium glycinate 300-500mg sleep onset latency RCT",
      "calcium citrate bedtime supplementation sleep quality"
    ],
    "pmc_queries": [
      "magnesium supplementation AND sleep quality AND adults",
      "calcium supplementation AND sleep architecture"
    ]
  }
}
```

### Continuous Learning

During training:
1. Reflector identifies knowledge gaps
2. Generates semantic + PMC queries
3. Downloader fetches new papers
4. Papers chunked and added to vector DB
5. Future evaluations use new research

---

## Best Practices

### Recommended Settings

**Quick Test (1 hour):**
```bash
python3 run_mix_optimization.py --use_case sleep --iterations 10 --batch_size 8
```

**Production Training (4-6 hours):**
```bash
python3 run_mix_optimization.py --all --iterations 20 --batch_size 12
```

**Deep Optimization (overnight):**
```bash
python3 run_mix_optimization.py --all --iterations 50 --batch_size 15
```

### Batch Size Guidelines

- **8-10**: Fast iteration, less stable
- **12-15**: Balanced (recommended)
- **20+**: Slower but more stable gradients

### Learning Rate Guidelines

- **0.1-0.2**: Conservative, slow convergence
- **0.3-0.4**: Balanced (recommended)
- **0.5+**: Aggressive, may overshoot

---

## Troubleshooting

### Training Not Improving

**Check:**
1. Is vector DB initialized? (`bestmove_vector_db/`)
2. Are research papers available?
3. Is learning rate too low?

**Solution:**
```bash
# Rebuild vector DB
python3 build_vector_store.py

# Increase learning rate
python3 run_mix_optimization.py --use_case sleep --learning_rate 0.4
```

### Scores Too Low (< 70)

**Likely causes:**
- Insufficient research in DB
- Formulation far from optimal
- Evaluation criteria too strict

**Solution:**
- Run more iterations
- Bootstrap with research queries
- Check `mix_research_queries.json`

### Training Too Slow

**Optimization:**
- Reduce batch size (--batch_size 8)
- Reduce iterations (--iterations 15)
- Reduce max_papers_per_gap in code (default 2)

---

## Next Steps

### After Training

1. **Review Outputs:**
   - Check `*_mix_final.json` for optimized formulations
   - Review `*_mix_training_history.json` for convergence

2. **Validate:**
   - Run additional test batches
   - Compare against literature
   - Check safety (doses within UL)

3. **Add Flavor Layer:**
   - Create `flavor_customizer.py`
   - Add sweetness preferences (none, light, moderate, sweet)
   - Add flavor intensity (subtle, moderate, bold)
   - Keep base minerals unchanged

4. **Production Integration:**
   - Export formulations to product specs
   - Add to ordering system
   - Create customer-facing descriptions

### Future Enhancements

- **Multi-objective optimization:** Balance efficacy, cost, taste
- **A/B testing framework:** Real customer feedback loop
- **Personalization layer:** Add optional modifiers on top of base mixes
- **Temporal optimization:** Morning vs. evening formulations

---

## Summary

The mix optimization system:
- ✅ Creates 3 research-backed base mixes
- ✅ Uses batch training (12+ diverse profiles)
- ✅ Averages gradients like SGD
- ✅ Continuously learns from new research
- ✅ Optimizes for population-wide performance
- ✅ Outputs single best formulation per use case
- ✅ Maintains safety limits
- ✅ Provides full reasoning + citations

**Ready to train your mixes!** 🚀


