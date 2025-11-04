# Quick Start: Mix Optimization

## What Was Built

A complete SGD-style training system for creating 3 optimized electrolyte base mixes:

### 🌙 Sleep Mix
- Optimized for: Sleep onset, maintenance, quality
- Training: 12+ diverse profiles per batch
- Focus: Mg glycinate (GABA), Ca:Mg ratio, minimal Na

### 💪 Active Mix  
- Optimized for: Exercise performance, recovery, hydration
- Training: Athletes, high sweat loss, muscle function
- Focus: Higher K/Na for sweat replacement, Mg for recovery

### ☀️ Daily Mix
- Optimized for: General wellness, maintenance
- Training: Broad population, all ages, activity levels
- Focus: Balanced baseline support, cardiovascular, bone health

---

## File Structure Created

```
✅ formulation_engines/
   ├── sleep_mix_optimizer.py         # Sleep formulation engine
   ├── active_mix_optimizer.py        # Active formulation engine
   ├── daily_mix_optimizer.py         # Daily formulation engine
   ├── batch_test_generator.py        # Generates 12+ test cases per batch
   └── mix_optimization_loop.py       # SGD training loop

✅ run_mix_optimization.py            # Main entry point (executable)
✅ mix_research_queries.json          # Research queries for each use case
✅ MIX_OPTIMIZATION_GUIDE.md          # Complete documentation
✅ QUICK_START_MIX_OPTIMIZATION.md    # This file
```

**Auto-generated during training:**
```
📊 sleep_mix_final.json               # Optimized sleep formulation
📊 active_mix_final.json              # Optimized active formulation  
📊 daily_mix_final.json               # Optimized daily formulation
📈 *_mix_training_history.json        # Training metrics & convergence
```

---

## Usage

### Train a Single Mix (Quick Test)

```bash
cd /home/jschu/projects/Agentic.RAG
source venv/bin/activate

# Train sleep mix (2-3 hours)
python3 run_mix_optimization.py --use_case sleep --iterations 10

# Train active mix
python3 run_mix_optimization.py --use_case active --iterations 10

# Train daily mix
python3 run_mix_optimization.py --use_case daily --iterations 10
```

### Train All Three Mixes (Production)

```bash
# This will take 6-8 hours total
python3 run_mix_optimization.py --all --iterations 20
```

### What You'll See

```
================================================================================
ITERATION 1/20
================================================================================

✅ Generated batch of 12 diverse test cases

  Evaluating test case 1/12...
    Score: 82/100
  Evaluating test case 2/12...
    Score: 79/100
  ...

📊 BATCH RESULTS:
   Average Score: 80.5/100
   Min Score: 76/100
   Max Score: 85/100
   🎉 NEW BEST! (previous: 0.0)

🤔 REFLECTION PHASE:
   Found 3 semantic queries, 3 PMC queries

📥 DOWNLOADING NEW RESEARCH:
   Papers downloaded: 4
   Chunks added: 156

📐 CALCULATING BATCH GRADIENTS:
   Averaged adjustments:
     magnesium: +8.2mg
     calcium: -3.1mg
     potassium: +5.7mg
     sodium: -2.4mg

🔧 APPLYING ADJUSTMENTS...
   Updated formulation:
     Mg: 408mg
     Ca: 197mg
     K:  256mg
     Na: 138mg
```

---

## Expected Results

After training, you'll get optimized formulations like:

### Sleep Mix Example
```json
{
  "formulation": {
    "magnesium": 425,
    "calcium": 210,
    "potassium": 265,
    "sodium": 140
  },
  "ratios": {
    "mg_ca": 2.02,
    "k_na": 1.89
  },
  "training_history": {
    "iterations": 18,
    "best_score": 87.3
  }
}
```

---

## Key Differences from Old System

| Feature | Old `sleep_support_engine.py` | New Mix Optimizers |
|---------|-------------------------------|-------------------|
| **Output** | Different mix per person | One optimal mix |
| **Training** | Single test cases | Batches of 12+ |
| **Optimization** | Rule-based adjustments | SGD-style gradients |
| **Use Case** | Long-term personalization | Short-term base mixes |
| **Complexity** | High (26+ variables) | Simple (4 minerals) |

**Both systems preserved!** Old system still available for future personalization.

---

## Next Steps After Training

### 1. Review Results
```bash
# Check optimized formulations
cat sleep_mix_final.json
cat active_mix_final.json
cat daily_mix_final.json

# Check training metrics
cat sleep_mix_training_history.json
```

### 2. Validate Formulations
- ✅ Doses within safe limits?
- ✅ Ratios make sense?
- ✅ Research citations support decisions?

### 3. Add Flavor Layer
Create customer preferences:
- Sweetness: none, light, moderate, sweet
- Flavor intensity: subtle, moderate, bold
- Keep base minerals unchanged

### 4. Production Integration
- Export to product specs
- Add to ordering system
- Create customer descriptions

---

## Troubleshooting

### "No module named formulation_engines"
```bash
# Make sure you're in the right directory
cd /home/jschu/projects/Agentic.RAG
source venv/bin/activate
```

### "Vector database not initialized"
```bash
# Build the vector store first
python3 build_vector_store.py
```

### Training too slow
```bash
# Use smaller batch and fewer iterations for testing
python3 run_mix_optimization.py --use_case sleep --iterations 5 --batch_size 8
```

### Scores not improving
- Let it run more iterations (convergence takes 15-25 iterations)
- Check that research papers are being downloaded
- Verify RAG system is working: `python3 test_claude_rag.py`

---

## Architecture Highlights

### Why Batch Training (like ML)?
- Tests formulation across diverse population
- Averages adjustments → stable convergence
- Prevents overfitting to single profile
- More robust optimal solution

### How It Learns
1. **Evaluation**: 8+ RAG queries per test case
2. **Reflection**: Identifies knowledge gaps
3. **Learning**: Downloads new research papers
4. **Adjustment**: Averages feedback across batch
5. **Iteration**: Repeat until convergence

### Safety Built-In
- Max dose caps (Mg: 500mg, Ca: 400mg, etc.)
- Ratio constraints (Mg:Ca ~2:1)
- Research validation required
- Gradual adjustments (learning rate 0.3)

---

## Summary

✅ **Created**: 3 single-mix optimizers + SGD training loop  
✅ **Preserved**: Old personalization engine for future use  
✅ **Training**: Batch-based (12+ diverse profiles)  
✅ **Research**: RAG-powered, continuously learning  
✅ **Output**: One optimal mix per use case  
✅ **Safe**: Built-in dose limits and validation  

**Ready to optimize your mixes!** 🚀

```bash
python3 run_mix_optimization.py --all --iterations 20
```


