#!/usr/bin/env python
"""
Agent Prompt Optimizer Tool

Interactive tool for optimizing agent prompts based on performance data.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime

from utils.decision_tracker import DecisionTracker
from utils.agent_prompt_optimizer import AgentPromptOptimizer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("prompt_optimizer_tool")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Optimize agent prompts")
    
    parser.add_argument("--agent", type=str, required=True,
                      help="Agent type to optimize (e.g., MarketAnalyst, RiskManager)")
    parser.add_argument("--days", type=int, default=30,
                      help="Number of days of performance data to analyze (default: 30)")
    parser.add_argument("--auto-apply", action="store_true",
                      help="Automatically apply suggested improvements")
    parser.add_argument("--output-dir", type=str, default="data/performance/prompts",
                      help="Directory for saving prompt versions")
    
    return parser.parse_args()

def print_prompt_analysis(agent_type: str, analysis: dict):
    """Print analysis of current prompt"""
    print("\n" + "-" * 80)
    print(f" CURRENT PROMPT ANALYSIS: {agent_type} ".center(80, "-"))
    print("-" * 80)
    
    if "current_prompt" in analysis:
        print("\nCurrent prompt:")
        print("-" * 40)
        print(analysis["current_prompt"])
        print("-" * 40)
    
    if "prompt_analysis" in analysis:
        pa = analysis["prompt_analysis"]
        print("\nAnalysis:")
        print(f"  Word count: {pa.get('word_count', 0)}")
        print(f"  Sentence count: {pa.get('sentence_count', 0)}")
        print(f"  Average sentence length: {pa.get('avg_sentence_length', 0):.1f} words")
        print(f"  Specificity score: {pa.get('specificity_score', 0)}/10")
        print(f"  Clarity score: {pa.get('clarity_score', 0)}/10")
        print(f"  Instruction count: {pa.get('instruction_count', 0)}")
        
        if pa.get('vague_terms'):
            print(f"  Vague terms: {', '.join(pa.get('vague_terms', []))}")
        
        if pa.get('ambiguity_issues'):
            print(f"  Ambiguity issues:")
            for issue in pa.get('ambiguity_issues', []):
                print(f"    - {issue}")
    
    if "improvement_areas" in analysis:
        areas = analysis["improvement_areas"]
        if areas:
            print("\nAreas needing improvement:")
            for area in areas:
                print(f"  - {area.replace('_', ' ').title()}")
        else:
            print("\nNo major improvement areas identified.")

def print_improvement_suggestions(analysis: dict):
    """Print suggested improvements for the prompt"""
    if "suggestions" not in analysis:
        print("\nNo improvement suggestions available.")
        return
    
    print("\n" + "-" * 80)
    print(" IMPROVEMENT SUGGESTIONS ".center(80, "-"))
    print("-" * 80)
    
    suggestions = analysis["suggestions"]
    for area, area_suggestions in suggestions.items():
        print(f"\n{area.replace('_', ' ').title()}:")
        for i, suggestion in enumerate(area_suggestions, 1):
            print(f"  {i}. {suggestion}")

def save_improved_prompt(agent_type: str, analysis: dict, output_dir: str):
    """Save the improved prompt to a file"""
    if "improved_prompt" not in analysis or not analysis["improved_prompt"]:
        print("\nNo improved prompt available to save.")
        return None
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{agent_type}_improved_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    
    # Save the improved prompt
    with open(filepath, "w") as f:
        f.write(analysis["improved_prompt"])
    
    print(f"\nImproved prompt saved to: {filepath}")
    return filepath

def get_user_approval(agent_type: str, analysis: dict):
    """Get user approval to apply the improved prompt"""
    if "improved_prompt" not in analysis or not analysis["improved_prompt"]:
        return False
    
    print("\n" + "-" * 80)
    print(" IMPROVED PROMPT ".center(80, "-"))
    print("-" * 80)
    
    print("\nImproved prompt:")
    print("-" * 40)
    print(analysis["improved_prompt"])
    print("-" * 40)
    
    # Ask for user approval
    while True:
        response = input("\nApply this improved prompt to the agent configuration? (y/n): ").strip().lower()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print("Please enter 'y' or 'n'.")

def main():
    """Main entry point"""
    args = parse_arguments()
    
    print("\n" + "=" * 80)
    print(" AGENT PROMPT OPTIMIZER TOOL ".center(80, "="))
    print("=" * 80 + "\n")
    
    try:
        # Initialize components
        decision_tracker = DecisionTracker()
        prompt_optimizer = AgentPromptOptimizer()
        
        # Get current prompt
        current_prompt = prompt_optimizer.get_agent_prompt(args.agent)
        if not current_prompt:
            print(f"Error: Could not find prompt for agent type: {args.agent}")
            return 1
        
        print(f"Agent: {args.agent}")
        print(f"Analysis period: {args.days} days")
        
        # Get performance data
        print("\nAnalyzing agent performance...")
        performance_data = decision_tracker.analyze_agent_performance(args.agent, days=args.days)
        
        # Generate improvement suggestions
        print("Generating prompt improvement suggestions...")
        improvement_results = prompt_optimizer.suggest_prompt_improvements(args.agent, performance_data)
        
        # Print current prompt analysis
        print_prompt_analysis(args.agent, improvement_results)
        
        # Print improvement suggestions
        print_improvement_suggestions(improvement_results)
        
        # Save improved prompt
        if "improved_prompt" in improvement_results and improvement_results["improved_prompt"]:
            save_improved_prompt(args.agent, improvement_results, args.output_dir)
            
            # Apply improvements if auto-apply or user approves
            apply_changes = args.auto_apply or get_user_approval(args.agent, improvement_results)
            
            if apply_changes:
                success, message = prompt_optimizer.apply_suggestions(
                    args.agent, improvement_results, manual_edit=False
                )
                
                if success:
                    print(f"\nSuccess: {message}")
                else:
                    print(f"\nError: {message}")
            else:
                print("\nPrompt improvements were not applied.")
        else:
            print("\nNo prompt improvements were generated.")
        
    except KeyboardInterrupt:
        print("\nOptimization interrupted by user")
    except Exception as e:
        logger.error(f"Error optimizing prompt: {str(e)}", exc_info=True)
        print(f"\nError: {str(e)}")
        return 1
    
    print("\n" + "=" * 80)
    print(" OPTIMIZATION COMPLETE ".center(80, "="))
    print("=" * 80 + "\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())