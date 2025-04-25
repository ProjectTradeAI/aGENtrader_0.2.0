#!/usr/bin/env python
"""
Agent Performance Analysis

Analyzes agent decision quality and consistency across trading sessions.
Generates performance reports and identifies areas for prompt improvement.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from utils.decision_tracker import DecisionTracker
from utils.agent_prompt_optimizer import AgentPromptOptimizer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("performance_analysis")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Analyze agent performance")
    
    parser.add_argument("--days", type=int, default=30,
                      help="Number of days to analyze (default: 30)")
    parser.add_argument("--agents", type=str, nargs="+",
                      default=["market_analyst", "strategy_manager", "risk_manager", "decision_agent"],
                      help="Agent types to analyze")
    parser.add_argument("--output-dir", type=str, default="data/performance/reports",
                      help="Directory for performance reports")
    parser.add_argument("--metrics", type=str, nargs="+",
                      default=["decision_consistency", "confidence_mean"],
                      help="Metrics to analyze")
    parser.add_argument("--compare", action="store_true",
                      help="Compare agents against each other")
    parser.add_argument("--analyze-conditions", action="store_true",
                      help="Analyze performance by market condition")
    
    return parser.parse_args()

def generate_performance_report(args) -> Dict[str, Any]:
    """
    Generate a comprehensive performance report.
    
    Args:
        args: Command line arguments
        
    Returns:
        Report data
    """
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize trackers
    decision_tracker = DecisionTracker()
    prompt_optimizer = AgentPromptOptimizer()
    
    # Collect metrics for each agent
    agent_metrics = {}
    for agent in args.agents:
        logger.info(f"Analyzing performance for {agent}...")
        metrics = decision_tracker.analyze_agent_performance(agent, days=args.days)
        agent_metrics[agent] = metrics
    
    # Generate prompt improvement suggestions for each agent
    improvement_suggestions = {}
    for agent in args.agents:
        logger.info(f"Generating prompt improvement suggestions for {agent}...")
        suggestions = decision_tracker.suggest_prompt_improvements(agent, days=args.days)
        improvement_suggestions[agent] = suggestions
    
    # Compare agents if requested
    comparison_data = {}
    if args.compare and len(args.agents) > 1:
        logger.info("Comparing agents...")
        for metric in args.metrics:
            # Extract the specific metric from each agent's performance data
            metric_data = {}
            for agent in args.agents:
                if metric == "decision_consistency":
                    # Extract consistency from decision types
                    decision_types = agent_metrics[agent].get("decision_types", {})
                    total_decisions = agent_metrics[agent].get("total_decisions", 0)
                    if total_decisions > 0:
                        consistency = max([count/total_decisions for count in decision_types.values()]) * 100
                        metric_data[agent] = {
                            "avg_value": consistency,
                            "sample_count": total_decisions
                        }
                elif metric == "confidence_mean":
                    # Extract average confidence
                    confidence = agent_metrics[agent].get("confidence_stats", {}).get("avg_confidence", 0)
                    metric_data[agent] = {
                        "avg_value": confidence,
                        "sample_count": agent_metrics[agent].get("total_decisions", 0)
                    }
                    
            comparison_data[metric] = {"comparison_data": metric_data}
    
    # Analyze market conditions if requested
    market_condition_analysis = {}
    if args.analyze_conditions:
        logger.info("Analyzing performance by market condition...")
        # Extract market condition data from agent metrics
        for agent in args.agents:
            market_condition_analysis[agent] = {}
            market_conditions = agent_metrics[agent].get("market_conditions", {})
            
            for condition, data in market_conditions.items():
                if condition != "unknown":
                    # Calculate consistency for this condition
                    actions = data.get("actions", {})
                    condition_count = data.get("count", 0)
                    
                    if condition_count > 0:
                        # Find most common decision in this condition
                        most_common = max(actions.items(), key=lambda x: x[1], default=("UNKNOWN", 0))
                        most_common_decision = most_common[0]
                        most_common_count = most_common[1]
                        
                        consistency_pct = (most_common_count / condition_count) * 100
                        
                        market_condition_analysis[agent][condition] = {
                            "consistency_pct": consistency_pct,
                            "most_common_decision": most_common_decision,
                            "decision_count": condition_count
                        }
    
    # Compile report data
    report = {
        "timestamp": datetime.now().isoformat(),
        "period_days": args.days,
        "agents_analyzed": args.agents,
        "metrics": args.metrics,
        "agent_metrics": agent_metrics,
        "improvement_suggestions": improvement_suggestions,
        "comparison_data": comparison_data,
        "market_condition_analysis": market_condition_analysis
    }
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"{args.output_dir}/performance_report_{timestamp}.json"
    
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Performance report saved to {report_file}")
    
    return report

def display_report_summary(report: Dict[str, Any]) -> None:
    """
    Display a summary of the performance report.
    
    Args:
        report: Performance report data
    """
    print("\n" + "=" * 80)
    print(" AGENT PERFORMANCE ANALYSIS SUMMARY ".center(80, "="))
    print("=" * 80)
    
    print(f"\nAnalysis period: {report['period_days']} days")
    print(f"Agents analyzed: {', '.join(report['agents_analyzed'])}")
    print(f"Generated at: {report['timestamp']}")
    
    # Summary by agent
    print("\n" + "-" * 80)
    print(" AGENT METRICS SUMMARY ".center(80, "-"))
    print("-" * 80)
    
    for agent, metrics in report["agent_metrics"].items():
        print(f"\n{agent.upper()}")
        print(f"  Decision count: {metrics.get('decision_count', 0)}")
        
        if metrics.get('confidence_stats', {}).get('mean') is not None:
            conf_mean = metrics['confidence_stats']['mean']
            conf_std = metrics['confidence_stats'].get('std_dev', 0)
            print(f"  Average confidence: {conf_mean:.2f}% (±{conf_std:.2f}%)")
        
        consistency_overall = metrics.get('consistency_metrics', {}).get('overall', {})
        if consistency_overall.get('avg_consistency_pct') is not None:
            print(f"  Decision consistency: {consistency_overall['avg_consistency_pct']:.2f}%")
        
        decision_types = metrics.get('decision_types', {})
        if decision_types:
            print("  Decision distribution:")
            for decision, count in decision_types.items():
                percentage = (count / metrics['decision_count']) * 100
                print(f"    {decision}: {count} ({percentage:.1f}%)")
    
    # Comparison data
    if report.get("comparison_data"):
        print("\n" + "-" * 80)
        print(" AGENT COMPARISON ".center(80, "-"))
        print("-" * 80)
        
        for metric, comparison in report["comparison_data"].items():
            print(f"\nMetric: {metric}")
            
            # Create a sorted list for better presentation
            sorted_agents = sorted(
                comparison.get('comparison_data', {}).items(),
                key=lambda x: x[1].get('avg_value', 0),
                reverse=True
            )
            
            for agent, data in sorted_agents:
                print(f"  {agent}: {data.get('avg_value', 0):.2f} (samples: {data.get('sample_count', 0)})")
    
    # Market condition analysis
    if report.get("market_condition_analysis"):
        print("\n" + "-" * 80)
        print(" MARKET CONDITION ANALYSIS ".center(80, "-"))
        print("-" * 80)
        
        for agent, conditions in report["market_condition_analysis"].items():
            print(f"\n{agent.upper()} - Performance by market condition:")
            
            for condition, analysis in conditions.items():
                if isinstance(analysis, dict) and analysis.get('decision_count', 0) > 0:
                    consistency = analysis.get('consistency_pct', 0)
                    decision = analysis.get('most_common_decision', 'UNKNOWN')
                    count = analysis.get('decision_count', 0)
                    
                    print(f"  {condition.upper()}: {consistency:.1f}% consistency " +
                         f"({decision} in {count} decisions)")
    
    print("\n" + "=" * 80)
    print(" PROMPT IMPROVEMENT RECOMMENDATIONS ".center(80, "="))
    print("=" * 80)
    
    # Display prompt improvement suggestions from our analysis
    print("\nBased on the performance analysis, the following prompt improvements are recommended:")
    
    # Extract recommendations from the improvement suggestions in the report
    recommendations = []
    
    for agent, suggestions in report.get("improvement_suggestions", {}).items():
        if suggestions.get("status") == "success":
            improvement_areas = suggestions.get("improvement_areas", [])
            
            for area in improvement_areas:
                area_suggestions = suggestions.get("suggestions", {}).get(area, [])
                
                # Take top suggestion from each area
                if area_suggestions and len(area_suggestions) > 0:
                    recommendations.append(f"- {agent}: {area_suggestions[0]}")
    
    # Add general recommendations if we have few specific ones
    if len(recommendations) < 2:
        # Extract suggestions from agent metrics the old way
        for agent, metrics in report["agent_metrics"].items():
            # Check for decision imbalance
            decision_types = metrics.get('decision_types', {})
            total_decisions = metrics.get('total_decisions', 0)
            
            if total_decisions > 0:
                max_pct = 0
                for action, count in decision_types.items():
                    pct = (count / total_decisions) * 100
                    max_pct = max(max_pct, pct)
                
                if max_pct > 70:
                    recommendations.append(
                        f"- {agent}: Improve balance of decisions - one action is being recommended {max_pct:.1f}% of the time."
                    )
            
            # Check confidence stats
            confidence = metrics.get('confidence_stats', {}).get('avg_confidence', 50)
            if confidence > 80:
                recommendations.append(
                    f"- {agent}: Consider recalibrating confidence - current average is {confidence:.1f}%, which may be overconfident."
                )
            elif confidence < 30:
                recommendations.append(
                    f"- {agent}: Consider recalibrating confidence - current average is {confidence:.1f}%, which may be underconfident."
                )
    
    # If still no recommendations, add general ones
    if len(recommendations) < 2:
        recommendations.extend([
            "- Consider adding more explicit decision criteria for boundary cases.",
            "- Include examples of high-quality decisions in agent prompts to serve as templates.",
            "- Specify how confidence should be calculated with clear guidelines for different levels."
        ])
    
    for rec in recommendations:
        print(rec)
    
    print("\n" + "=" * 80)
    print(" END OF REPORT ".center(80, "="))
    print("=" * 80 + "\n")

def main():
    """Main entry point"""
    args = parse_arguments()
    
    print("\n" + "=" * 80)
    print(" AGENT PERFORMANCE ANALYSIS ".center(80, "="))
    print("=" * 80 + "\n")
    
    try:
        # Generate performance report
        report = generate_performance_report(args)
        
        # Display summary
        display_report_summary(report)
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
    except Exception as e:
        logger.error(f"Error in performance analysis: {str(e)}", exc_info=True)
        print(f"\nError: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())