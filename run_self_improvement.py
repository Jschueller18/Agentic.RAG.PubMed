#!/usr/bin/env python3
"""
Run the self-improving algorithm system

Usage:
    python3 run_self_improvement.py

This will:
1. Load the sleep support engine
2. Generate test cases
3. Run parallel RAG evaluation (8 queries per test)
4. Automatically adjust weights based on research
5. Re-test and keep improvements
6. Save updated algorithm
"""

import sys
import os

# Add formulation_engines to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'formulation_engines'))

from improvement_loop import ImprovementLoop, generate_test_cases


def main():
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║           BESTMOVE SELF-IMPROVING ALGORITHM SYSTEM                        ║
║                                                                           ║
║   Continuously refines electrolyte formulations using RAG research        ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
""")
    
    # Load API key from bashrc if not in environment
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("📋 Loading API key from ~/.bashrc...")
        bashrc_path = os.path.expanduser("~/.bashrc")
        try:
            with open(bashrc_path, 'r') as f:
                for line in f:
                    if 'ANTHROPIC_API_KEY' in line and 'export' in line:
                        # Extract key from line like: export ANTHROPIC_API_KEY="sk-ant-..."
                        key = line.split('=', 1)[1].strip().strip('"').strip("'")
                        os.environ["ANTHROPIC_API_KEY"] = key
                        print(f"✅ Loaded API key: {key[:15]}...{key[-10:]}")
                        break
        except Exception as e:
            print(f"❌ ERROR: Could not load API key from ~/.bashrc: {e}")
            sys.exit(1)
    
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ ERROR: ANTHROPIC_API_KEY not found!")
        print("   Add to ~/.bashrc: export ANTHROPIC_API_KEY=\"your-key-here\"")
        sys.exit(1)
    
    # Initialize system
    loop = ImprovementLoop("sleep_support")
    
    # Generate test cases
    print("\n📝 Generating test cases...")
    test_cases = generate_test_cases()
    print(f"✅ Created {len(test_cases)} diverse test scenarios")
    
    # Run improvement cycle
    print("\n🚀 Starting self-improvement cycle...")
    print("   This will:")
    print("   • Calculate recommendations for each test case")
    print("   • Run 8 parallel RAG queries to validate doses")
    print("   • Grade each mineral (0-100)")
    print("   • Adjust algorithm weights based on research")
    print("   • Re-test and keep improvements")
    print("\n   Estimated time: 5-10 minutes\n")
    print("🚀 Beginning automated self-improvement...\n")

    try:
        loop.run_improvement_cycle(test_cases, max_iterations=3)
        
        print("\n" + "="*80)
        print("✅ SELF-IMPROVEMENT COMPLETE!")
        print("="*80)
        print("\nThe algorithm has been improved based on latest research.")
        print("Updated weights saved to: formulation_engines/sleep_weights.json")
        print("\nYou can now:")
        print("  1. Run again with new test cases to continue improving")
        print("  2. Use the updated algorithm for customer calculations")
        print("  3. Review weight changes in sleep_weights.json")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("   Progress has been saved")
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

