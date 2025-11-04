# System Architecture Overview

## Two Parallel Systems (Both Preserved)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AGENTIC RAG INFRASTRUCTURE                       │
│  • Vector Database (Qdrant)                                         │
│  • Research Papers (PMC)                                            │
│  • RAG Evaluation (8+ queries)                                      │
│  • Knowledge Gap Detection                                          │
│  • Research Downloader                                              │
└─────────────────────────────────────────────────────────────────────┘
                            ▲         ▲
                            │         │
        ┌───────────────────┘         └───────────────────┐
        │                                                 │
┌───────▼──────────────────┐                 ┌───────────▼─────────────┐
│  OLD SYSTEM (Preserved)  │                 │  NEW SYSTEM (Created)   │
│  Personalization Engine  │                 │  Single-Mix Optimizers  │
├──────────────────────────┤                 ├─────────────────────────┤
│ sleep_support_engine.py  │                 │ sleep_mix_optimizer.py  │
│ improvement_loop.py      │                 │ active_mix_optimizer.py │
│                          │                 │ daily_mix_optimizer.py  │
│ PURPOSE:                 │                 │ batch_test_generator.py │
│ - Personalized mixes     │                 │ mix_optimization_loop.py│
│ - Different per person   │                 │                         │
│ - Complex rules (26+ var)│                 │ PURPOSE:                │
│ - Long-term vision       │                 │ - 3 base mixes          │
│                          │                 │ - Same for everyone     │
│ INPUT:                   │                 │ - SGD training (12+)    │
│ {age, sex, weight,       │                 │ - Short-term launch     │
│  sleep_issues, ...}      │                 │                         │
│                          │                 │ INPUT:                  │
│ OUTPUT:                  │                 │ Batch of diverse        │
│ Personalized formulation │                 │ test cases              │
│                          │                 │                         │
│ USE CASE:                │                 │ OUTPUT:                 │
│ Premium customization    │                 │ ONE optimal mix per     │
│                          │                 │ use case (Sleep/        │
│                          │                 │ Active/Daily)           │
│                          │                 │                         │
│                          │                 │ USE CASE:               │
│                          │                 │ Base product line       │
└──────────────────────────┘                 └─────────────────────────┘
```

---

## New System: Mix Optimization Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    run_mix_optimization.py                      │
│                    (Main Entry Point)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
   ┌─────────┐                    ┌─────────┐
   │  SLEEP  │                    │ ACTIVE  │
   │   MIX   │                    │   MIX   │
   └─────────┘                    └─────────┘
         │                               │
         └───────────┬───────────────────┘
                     │
                     ▼
              ┌──────────┐
              │  DAILY   │
              │   MIX    │
              └──────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │ MixOptimizationLoop    │
        │ (SGD-Style Training)   │
        └────────────┬───────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │Batch    │ │Parallel │ │Reasoning│
   │Test     │ │Evaluator│ │Reflector│
   │Gen      │ │(RAG)    │ │(Meta)   │
   └─────────┘ └─────────┘ └─────────┘
         │           │           │
         └───────────┼───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │TargetedResearch       │
         │Downloader             │
         │(Knowledge Gap Fill)   │
         └───────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │ Vector Database       │
         │ (Continuously Growing)│
         └───────────────────────┘
```

---

## Training Loop Detail

```
START
  │
  ▼
┌────────────────────────┐
│ 1. BATCH GENERATION    │  ◄─────┐
│ Generate 12+ diverse   │         │
│ test cases             │         │
└───────────┬────────────┘         │
            │                      │
            ▼                      │
┌────────────────────────┐         │
│ 2. EVALUATION          │         │
│ • Test formulation     │         │
│ • Run 8+ RAG queries   │         │
│ • Grade minerals       │         │
│ • Calculate avg score  │         │
└───────────┬────────────┘         │
            │                      │
            ▼                      │
┌────────────────────────┐         │
│ 3. REFLECTION          │         │
│ • Identify gaps        │         │
│ • Generate queries     │         │
└───────────┬────────────┘         │
            │                      │
            ▼                      │
┌────────────────────────┐         │
│ 4. LEARNING            │         │
│ • Download papers      │         │
│ • Add to vector DB     │         │
└───────────┬────────────┘         │
            │                      │
            ▼                      │
┌────────────────────────┐         │
│ 5. GRADIENT CALC       │         │
│ • Parse suggestions    │         │
│ • Average across batch │         │
│ • Apply learning rate  │         │
└───────────┬────────────┘         │
            │                      │
            ▼                      │
┌────────────────────────┐         │
│ 6. UPDATE              │         │
│ • Adjust formulation   │         │
│ • Save weights         │         │
└───────────┬────────────┘         │
            │                      │
            ▼                      │
┌────────────────────────┐         │
│ 7. CONVERGENCE CHECK   │         │
│ Improved? ─────Yes─────┘         │
│     │                            │
│     No                           │
│     ▼                            │
│   STOP                           │
└──────────────────────────────────┘

OUTPUTS:
• *_mix_final.json (optimized formulation)
• *_mix_training_history.json (metrics)
```

---

## File Structure

```
Agentic.RAG/
│
├── formulation_engines/
│   ├── [OLD - PRESERVED]
│   │   ├── sleep_support_engine.py      (Personalization)
│   │   └── improvement_loop.py          (Old training loop)
│   │
│   ├── [NEW - CREATED]
│   │   ├── sleep_mix_optimizer.py       ✅ Single sleep mix
│   │   ├── active_mix_optimizer.py      ✅ Single active mix
│   │   ├── daily_mix_optimizer.py       ✅ Single daily mix
│   │   ├── batch_test_generator.py      ✅ Batch generation
│   │   └── mix_optimization_loop.py     ✅ SGD training
│   │
│   └── [SHARED - REUSED]
│       ├── parallel_evaluator.py        (RAG evaluation)
│       ├── reasoning_reflector.py       (Meta-reasoning)
│       ├── targeted_research_downloader.py
│       └── pmc_query_optimizer.py
│
├── [NEW - CREATED]
│   ├── run_mix_optimization.py          ✅ Main entry point
│   ├── mix_research_queries.json        ✅ Bootstrap queries
│   ├── MIX_OPTIMIZATION_GUIDE.md        ✅ Complete guide
│   ├── QUICK_START_MIX_OPTIMIZATION.md  ✅ Quick start
│   ├── MIX_OPTIMIZATION_IMPLEMENTATION_SUMMARY.md ✅
│   └── SYSTEM_ARCHITECTURE_OVERVIEW.md  ✅ This file
│
├── [AUTO-GENERATED DURING TRAINING]
│   ├── sleep_mix_final.json             (Output)
│   ├── active_mix_final.json            (Output)
│   ├── daily_mix_final.json             (Output)
│   ├── sleep_mix_training_history.json  (Metrics)
│   ├── active_mix_training_history.json (Metrics)
│   └── daily_mix_training_history.json  (Metrics)
│
└── [EXISTING INFRASTRUCTURE]
    ├── bestmove_vector_db/              (Vector store)
    ├── pmc_targeted_papers/             (Research papers)
    ├── build_vector_store.py
    └── ...
```

---

## Data Flow

```
1. USER COMMAND
   python3 run_mix_optimization.py --use_case sleep

2. OPTIMIZER INITIALIZATION
   sleep_mix_optimizer.py
   └─> Loads default weights (Mg:400, Ca:200, K:250, Na:150)

3. BATCH GENERATION
   batch_test_generator.py
   └─> Creates 12 diverse test cases:
       • Ages: 19, 28, 35, 42, 51, 58, 65, 72, 78, ...
       • Mix of male/female, sleep issues, intakes

4. EVALUATION (Per Test Case)
   parallel_evaluator.py
   ├─> Query 1: "magnesium 400mg sleep quality women age 35"
   ├─> Query 2: "calcium 200mg sleep support"
   ├─> Query 3: "Mg:Ca ratio 2:1 GABA production"
   ├─> Query 4-8: (interaction, demographic, condition)
   └─> Grades: Mg=85, Ca=82, K=79, Na=88 → Avg=83.5

5. BATCH AGGREGATION
   mix_optimization_loop.py
   └─> Average across 12 cases: 83.5, 81.2, 86.1, ... → Batch avg: 82.7

6. REFLECTION
   reasoning_reflector.py
   └─> "Need more research on calcium timing for sleep"
   └─> Queries: ["calcium supplementation AND sleep timing"]

7. RESEARCH DOWNLOAD
   targeted_research_downloader.py
   └─> Downloads 3 papers, adds 147 chunks to vector DB

8. GRADIENT CALCULATION
   mix_optimization_loop.py
   └─> Case 1: Mg +10mg, Ca -5mg
   └─> Case 2: Mg +8mg, Ca -3mg
   └─> ...
   └─> Average: Mg +9mg, Ca -4mg
   └─> With LR 0.3: Mg +3mg, Ca -1mg

9. UPDATE
   sleep_mix_optimizer.py
   └─> New: Mg:403, Ca:199, K:253, Na:148

10. CONVERGENCE
    After 18 iterations:
    └─> Best formulation: Mg:425, Ca:210, K:265, Na:140
    └─> Score: 87.3
    └─> Saved to sleep_mix_final.json
```

---

## Comparison: Old vs New

| Aspect | Old (Personalization) | New (Single-Mix) |
|--------|----------------------|------------------|
| **Output** | Different for each person | One per use case |
| **Variables** | 26+ (age, sex, weight, ...) | 4 (Mg, Ca, K, Na) |
| **Training** | Single test cases | Batches of 12+ |
| **Complexity** | High (rules + multipliers) | Simple (4 doses) |
| **Time to Market** | Long (needs extensive validation) | Short (3 fixed formulas) |
| **Use Case** | Premium personalization | Base product line |
| **Status** | Preserved for future | Active development |

**Both systems coexist!** Use new for quick launch, add old for premium tier later.

---

## Success Criteria

### Development ✅
- [x] Three optimizer engines created
- [x] Batch generator creates diverse cases
- [x] SGD training loop implemented
- [x] RAG integration working
- [x] Research download functional
- [x] All files tested successfully

### Training (Next Step)
- [ ] Run: `python3 run_mix_optimization.py --all --iterations 20`
- [ ] Average scores > 80 per mix
- [ ] Convergence in < 25 iterations
- [ ] Doses within safety limits
- [ ] Research citations present

### Production (Future)
- [ ] Add flavor customization
- [ ] Customer descriptions written
- [ ] Manufacturing specs created
- [ ] Ordering system integration
- [ ] Launch to customers

---

## Next Commands

### Test the System
```bash
cd /home/jschu/projects/Agentic.RAG
source venv/bin/activate

# Quick test (1-2 hours)
python3 run_mix_optimization.py --use_case sleep --iterations 5
```

### Production Training
```bash
# Full training (6-8 hours - run overnight)
python3 run_mix_optimization.py --all --iterations 20
```

### Review Results
```bash
# Check optimized formulations
cat sleep_mix_final.json
cat active_mix_final.json  
cat daily_mix_final.json

# Check training metrics
cat sleep_mix_training_history.json
```

---

## Summary

**What was built:**
- ✅ 3 single-mix optimizers (sleep, active, daily)
- ✅ Batch test generator (12+ diverse cases)
- ✅ SGD-style training loop
- ✅ RAG-powered evaluation
- ✅ Research integration
- ✅ Complete documentation

**What was preserved:**
- ✅ Old personalization engine
- ✅ All existing infrastructure
- ✅ Vector database
- ✅ Research papers

**Ready to:**
- 🚀 Train all three mixes
- 🚀 Launch base product line
- 🚀 Add flavor customization
- 🚀 Scale to customers

**Time investment:**
- Development: ✅ Complete
- Training: ⏳ 6-8 hours (automated)
- Launch: ⏳ 1-2 weeks (add flavors)


