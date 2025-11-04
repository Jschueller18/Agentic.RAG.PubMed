#!/usr/bin/env python3
"""
Main Runner for Mix Optimization
Trains all three base mixes: Sleep, Active, Daily

Usage:
    python3 run_mix_optimization.py --use_case sleep --iterations 20 --batch_size 12
    python3 run_mix_optimization.py --all --iterations 15
"""

import argparse
import sys
import os
from datetime import datetime

# Add formulation_engines to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'formulation_engines'))

from formulation_engines.mix_optimization_loop import MixOptimizationLoop


def train_single_mix(use_case: str, iterations: int, batch_size: int, learning_rate: float):
    """Train a single mix"""
    print(f"\n{'#'*80}")
    print(f"# TRAINING {use_case.upper()} MIX")
    print(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}\n")
    
    try:
        loop = MixOptimizationLoop(
            use_case=use_case,
            batch_size=batch_size
        )
        
        results = loop.run(
            iterations=iterations,
            learning_rate=learning_rate
        )
        
        print(f"\n✅ {use_case.upper()} MIX TRAINING COMPLETE")
        print(f"   Best Score: {results['best_score']:.1f}/100")
        print(f"   Iterations: {results['iterations']}")
        print(f"   Final Formulation:")
        if results['best_formulation']:
            for mineral, amount in results['best_formulation'].items():
                print(f"     {mineral.capitalize()}: {amount}mg")
        
        return results
        
    except Exception as e:
        print(f"\n❌ ERROR training {use_case} mix: {e}")
        import traceback
        traceback.print_exc()
        return None


def train_all_mixes(iterations: int, batch_size: int, learning_rate: float):
    """Train all three mixes sequentially"""
    print(f"\n{'='*80}")
    print(f"TRAINING ALL THREE BASE MIXES")
    print(f"Sleep | Active | Daily")
    print(f"Iterations: {iterations} | Batch Size: {batch_size} | Learning Rate: {learning_rate}")
    print(f"{'='*80}\n")
    
    results = {}
    use_cases = ["sleep", "active", "daily"]
    
    for use_case in use_cases:
        result = train_single_mix(use_case, iterations, batch_size, learning_rate)
        results[use_case] = result
        
        if result is None:
            print(f"\n⚠️  Stopping: Failed to train {use_case} mix")
            break
    
    # Summary
    print(f"\n{'='*80}")
    print(f"TRAINING SUMMARY - ALL MIXES")
    print(f"{'='*80}\n")
    
    for use_case, result in results.items():
        if result:
            print(f"{use_case.upper()} MIX:")
            print(f"  Score: {result['best_score']:.1f}/100")
            print(f"  Iterations: {result['iterations']}")
            if result['best_formulation']:
                form = result['best_formulation']
                print(f"  Formulation: Mg {form['magnesium']}mg | Ca {form['calcium']}mg | K {form['potassium']}mg | Na {form['sodium']}mg")
            print()
    
    print(f"{'='*80}\n")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Train electrolyte mix formulations using RAG-powered optimization"
    )
    
    parser.add_argument(
        "--use_case",
        type=str,
        choices=["sleep", "active", "daily"],
        help="Which mix to train (sleep, active, or daily)"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Train all three mixes sequentially"
    )
    
    parser.add_argument(
        "--iterations",
        type=int,
        default=20,
        help="Number of training iterations (default: 20)"
    )
    
    parser.add_argument(
        "--batch_size",
        type=int,
        default=12,
        help="Number of test cases per batch (default: 12)"
    )
    
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=0.3,
        help="Learning rate for gradient descent (default: 0.3)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.all and not args.use_case:
        parser.error("Must specify either --use_case or --all")
    
    if args.all and args.use_case:
        parser.error("Cannot specify both --use_case and --all")
    
    # Run training
    if args.all:
        results = train_all_mixes(
            iterations=args.iterations,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate
        )
    else:
        results = train_single_mix(
            use_case=args.use_case,
            iterations=args.iterations,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate
        )
    
    print("\n🎉 All training complete!")
    print(f"Check the *_mix_final.json files for optimized formulations")
    print(f"Check the *_mix_training_history.json files for training metrics\n")


if __name__ == "__main__":
    main()


