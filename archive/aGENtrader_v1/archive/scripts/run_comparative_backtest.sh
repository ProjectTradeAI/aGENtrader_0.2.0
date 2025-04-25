#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values for backtest parameters
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE="2025-03-01"
END_DATE="2025-04-01"
BALANCE=10000
RISK=0.02
DECISION_INTERVAL=2
MIN_CONFIDENCE=75
OUTPUT_DIR="comparative_backtest_results"

# Function to display usage information
function display_usage {
    echo -e "${YELLOW}Comparative Backtest Runner${NC}"
    echo -e "Runs backtests with both TinyLlama and Mixtral models for performance comparison"
    echo
    echo -e "Usage: $0 [options]"
    echo -e "Options:"
    echo -e "  --symbol SYMBOL       Trading symbol (default: $SYMBOL)"
    echo -e "  --interval INTERVAL   Time interval (default: $INTERVAL)"
    echo -e "  --start_date DATE     Start date in YYYY-MM-DD format (default: $START_DATE)"
    echo -e "  --end_date DATE       End date in YYYY-MM-DD format (default: $END_DATE)"
    echo -e "  --balance AMOUNT      Initial balance (default: $BALANCE)"
    echo -e "  --risk FACTOR         Risk factor (default: $RISK)"
    echo -e "  --decision_interval N Decision interval in hours (default: $DECISION_INTERVAL)"
    echo -e "  --min_confidence N    Minimum confidence level (default: $MIN_CONFIDENCE)"
    echo -e "  --output_dir DIR      Output directory (default: $OUTPUT_DIR)"
    echo -e "  --help                Display this help message"
    echo
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --symbol)
            SYMBOL="$2"
            shift 2
            ;;
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --start_date)
            START_DATE="$2"
            shift 2
            ;;
        --end_date)
            END_DATE="$2"
            shift 2
            ;;
        --balance)
            BALANCE="$2"
            shift 2
            ;;
        --risk)
            RISK="$2"
            shift 2
            ;;
        --decision_interval)
            DECISION_INTERVAL="$2"
            shift 2
            ;;
        --min_confidence)
            MIN_CONFIDENCE="$2"
            shift 2
            ;;
        --output_dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --help)
            display_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            display_usage
            exit 1
            ;;
    esac
done

echo -e "${GREEN}Comparative Backtest: TinyLlama vs Mixtral${NC}"
echo -e "${YELLOW}Parameters:${NC}"
echo -e "  Symbol: $SYMBOL"
echo -e "  Interval: $INTERVAL"
echo -e "  Date Range: $START_DATE to $END_DATE"
echo -e "  Initial Balance: $BALANCE"
echo -e "  Risk Factor: $RISK"
echo -e "  Decision Interval: $DECISION_INTERVAL hours"
echo -e "  Minimum Confidence: $MIN_CONFIDENCE%"
echo -e "  Output Directory: $OUTPUT_DIR"
echo

# Verify Mixtral model is available
echo -e "${GREEN}Checking Mixtral model availability...${NC}"
FILE_DETAILS=$(ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "ls -lah /home/ec2-user/aGENtrader/models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf 2>/dev/null || echo 'File not found'")

if [[ "$FILE_DETAILS" == *"File not found"* ]]; then
    echo -e "${RED}Mixtral model file not found. Cannot run comparative backtest.${NC}"
    echo -e "${YELLOW}Please check the download status with ./check_mixtral_progress.sh${NC}"
    exit 1
fi

# Create Python script for running comparative backtests
cat > comparative_backtest.py << 'PYTHONSCRIPT'
"""
Comparative Backtest Runner

This script runs backtests with both TinyLlama and Mixtral models
and compares their performance.
"""

import os
import sys
import json
import argparse
import shutil
from datetime import datetime
import time

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Comparative Backtest Runner")
    
    parser.add_argument("--symbol", type=str, default="BTCUSDT",
                        help="Trading symbol")
    parser.add_argument("--interval", type=str, default="1h",
                        help="Time interval")
    parser.add_argument("--start_date", type=str, default="2025-03-01",
                        help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end_date", type=str, default="2025-04-01",
                        help="End date in YYYY-MM-DD format")
    parser.add_argument("--balance", type=float, default=10000.0,
                        help="Initial balance")
    parser.add_argument("--risk", type=float, default=0.02,
                        help="Risk factor")
    parser.add_argument("--decision_interval", type=int, default=2,
                        help="Decision interval in hours")
    parser.add_argument("--min_confidence", type=int, default=75,
                        help="Minimum confidence level")
    parser.add_argument("--output_dir", type=str, default="comparative_backtest_results",
                        help="Output directory")
    
    return parser.parse_args()

def backup_autogen_config():
    """Backup the current AutoGen configuration"""
    config_path = "utils/llm_integration/autogen_integration.py"
    backup_path = f"{config_path}.comparative_backup"
    
    if os.path.exists(config_path):
        shutil.copy2(config_path, backup_path)
        print(f"Backed up AutoGen config to {backup_path}")
        return True
    else:
        print(f"Error: Could not find AutoGen config at {config_path}")
        return False

def restore_autogen_config():
    """Restore the AutoGen configuration from backup"""
    config_path = "utils/llm_integration/autogen_integration.py"
    backup_path = f"{config_path}.comparative_backup"
    
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, config_path)
        print(f"Restored AutoGen config from {backup_path}")
        return True
    else:
        print(f"Error: Could not find backup config at {backup_path}")
        return False

def run_backtest_with_model(args, model_name, output_file):
    """Run a backtest with the specified model"""
    from run_simplified_full_backtest import run_backtest
    
    print(f"\n{'='*80}")
    print(f"Running backtest with {model_name} model")
    print(f"{'='*80}")
    
    # Run the backtest
    results = run_backtest(
        symbol=args.symbol,
        interval=args.interval,
        start_date=args.start_date,
        end_date=args.end_date,
        initial_balance=args.balance,
        risk_factor=args.risk,
        decision_interval_hours=args.decision_interval,
        min_confidence=args.min_confidence,
        verbose=True
    )
    
    # Save the results
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Saved {model_name} results to {output_file}")
    return results

def setup_tinyllama_config():
    """Set up the TinyLlama configuration"""
    config_path = "utils/llm_integration/autogen_integration.py"
    
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Ensure TinyLlama is configured
    if "TinyLlama" not in content:
        # Replace Mixtral with TinyLlama
        content = content.replace(
            '"model": "local-mixtral-8x7b-instruct"',
            '"model": "TinyLlama-1.1B-Chat-v1.0"'
        )
        
        content = content.replace(
            'mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf',
            'tinyllama-1.1b-chat-v1.0.Q5_K_M.gguf'
        )
        
        with open(config_path, 'w') as f:
            f.write(content)
        
        print("Updated config to use TinyLlama")
    else:
        print("Config already set to use TinyLlama")

def setup_mixtral_config():
    """Set up the Mixtral configuration"""
    config_path = "utils/llm_integration/autogen_integration.py"
    
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Ensure Mixtral is configured
    if "mixtral-8x7b-instruct" not in content:
        # Replace TinyLlama with Mixtral
        content = content.replace(
            '"model": "TinyLlama-1.1B-Chat-v1.0"',
            '"model": "local-mixtral-8x7b-instruct"'
        )
        
        content = content.replace(
            'tinyllama-1.1b-chat-v1.0.Q5_K_M.gguf',
            'mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf'
        )
        
        with open(config_path, 'w') as f:
            f.write(content)
        
        print("Updated config to use Mixtral")
    else:
        print("Config already set to use Mixtral")

def compare_results(tinyllama_results, mixtral_results, output_file):
    """Compare the results from both models"""
    comparison = {
        "timestamp": datetime.now().isoformat(),
        "comparison_summary": {
            "tinyllama_net_profit": tinyllama_results.get("portfolio", {}).get("net_profit", 0),
            "mixtral_net_profit": mixtral_results.get("portfolio", {}).get("net_profit", 0),
            "profit_difference": mixtral_results.get("portfolio", {}).get("net_profit", 0) - 
                                tinyllama_results.get("portfolio", {}).get("net_profit", 0),
            "tinyllama_win_rate": tinyllama_results.get("trades", {}).get("win_rate", 0),
            "mixtral_win_rate": mixtral_results.get("trades", {}).get("win_rate", 0),
            "win_rate_difference": mixtral_results.get("trades", {}).get("win_rate", 0) - 
                                  tinyllama_results.get("trades", {}).get("win_rate", 0),
            "tinyllama_max_drawdown": tinyllama_results.get("risk", {}).get("max_drawdown", 0),
            "mixtral_max_drawdown": mixtral_results.get("risk", {}).get("max_drawdown", 0),
            "drawdown_difference": mixtral_results.get("risk", {}).get("max_drawdown", 0) - 
                                  tinyllama_results.get("risk", {}).get("max_drawdown", 0),
            "tinyllama_sharpe_ratio": tinyllama_results.get("metrics", {}).get("sharpe_ratio", 0),
            "mixtral_sharpe_ratio": mixtral_results.get("metrics", {}).get("sharpe_ratio", 0),
            "sharpe_ratio_difference": mixtral_results.get("metrics", {}).get("sharpe_ratio", 0) - 
                                      tinyllama_results.get("metrics", {}).get("sharpe_ratio", 0),
        },
        "tinyllama_results": tinyllama_results,
        "mixtral_results": mixtral_results
    }
    
    # Calculate percentage differences
    tl_profit = tinyllama_results.get("portfolio", {}).get("net_profit", 0)
    mx_profit = mixtral_results.get("portfolio", {}).get("net_profit", 0)
    
    if tl_profit != 0:
        profit_pct_diff = ((mx_profit - tl_profit) / abs(tl_profit)) * 100
        comparison["comparison_summary"]["profit_percentage_difference"] = profit_pct_diff
    
    # Save the comparison
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    print(f"Saved comparison results to {output_file}")
    return comparison

def print_comparison_summary(comparison):
    """Print a summary of the comparison results"""
    summary = comparison["comparison_summary"]
    
    print("\n" + "="*80)
    print("COMPARATIVE BACKTEST RESULTS SUMMARY")
    print("="*80)
    
    print("\n{:<20} {:<15} {:<15} {:<15}".format("Metric", "TinyLlama", "Mixtral", "Difference"))
    print("-"*70)
    
    print("{:<20} {:<15.2f} {:<15.2f} {:<15.2f}".format(
        "Net Profit ($)", 
        summary["tinyllama_net_profit"],
        summary["mixtral_net_profit"],
        summary["profit_difference"]
    ))
    
    if "profit_percentage_difference" in summary:
        print("{:<20} {:<15} {:<15} {:<15.2f}%".format(
            "Profit Change", "", "", summary["profit_percentage_difference"]
        ))
    
    print("{:<20} {:<15.2f}% {:<15.2f}% {:<15.2f}%".format(
        "Win Rate", 
        summary["tinyllama_win_rate"] * 100,
        summary["mixtral_win_rate"] * 100,
        summary["win_rate_difference"] * 100
    ))
    
    print("{:<20} {:<15.2f}% {:<15.2f}% {:<15.2f}%".format(
        "Max Drawdown", 
        summary["tinyllama_max_drawdown"] * 100,
        summary["mixtral_max_drawdown"] * 100,
        summary["drawdown_difference"] * 100
    ))
    
    print("{:<20} {:<15.2f} {:<15.2f} {:<15.2f}".format(
        "Sharpe Ratio", 
        summary["tinyllama_sharpe_ratio"],
        summary["mixtral_sharpe_ratio"],
        summary["sharpe_ratio_difference"]
    ))
    
    print("\n" + "="*80)
    
    # Add conclusions
    winner = "Mixtral" if summary["profit_difference"] > 0 else "TinyLlama"
    
    print(f"\nCONCLUSION: {winner} performed better in this backtest period")
    
    if "profit_percentage_difference" in summary:
        pct_diff = summary["profit_percentage_difference"]
        print(f"Profit improvement: {abs(pct_diff):.2f}% {'increase' if pct_diff > 0 else 'decrease'}")
    
    print("\n" + "="*80)

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Create a timestamp for this comparison
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define output files
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    tinyllama_output = os.path.join(output_dir, f"{timestamp}_tinyllama_results.json")
    mixtral_output = os.path.join(output_dir, f"{timestamp}_mixtral_results.json")
    comparison_output = os.path.join(output_dir, f"{timestamp}_comparison.json")
    
    # Backup the current AutoGen configuration
    if not backup_autogen_config():
        print("Failed to backup AutoGen config. Aborting.")
        return
    
    try:
        # Run with TinyLlama first
        setup_tinyllama_config()
        tinyllama_results = run_backtest_with_model(args, "TinyLlama", tinyllama_output)
        
        # Give the system some time to cool down
        print("Waiting 10 seconds before running the next backtest...")
        time.sleep(10)
        
        # Run with Mixtral next
        setup_mixtral_config()
        mixtral_results = run_backtest_with_model(args, "Mixtral", mixtral_output)
        
        # Compare the results
        comparison = compare_results(tinyllama_results, mixtral_results, comparison_output)
        
        # Print the comparison summary
        print_comparison_summary(comparison)
        
    finally:
        # Restore the original AutoGen configuration
        restore_autogen_config()
    
    print("\nComparative backtest completed!")

if __name__ == "__main__":
    main()
PYTHONSCRIPT

# Upload the script to EC2
echo -e "${GREEN}Uploading comparative backtest script to EC2...${NC}"
scp -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 comparative_backtest.py ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/comparative_backtest.py

# Create the script to run on EC2
cat > run_remote_comparative_backtest.sh << REMOTESCRIPT
#!/bin/bash

cd /home/ec2-user/aGENtrader

echo "Running comparative backtest..."
python comparative_backtest.py \\
  --symbol "$SYMBOL" \\
  --interval "$INTERVAL" \\
  --start_date "$START_DATE" \\
  --end_date "$END_DATE" \\
  --balance "$BALANCE" \\
  --risk "$RISK" \\
  --decision_interval "$DECISION_INTERVAL" \\
  --min_confidence "$MIN_CONFIDENCE" \\
  --output_dir "$OUTPUT_DIR"
REMOTESCRIPT

# Upload the script to EC2
echo -e "${GREEN}Uploading remote execution script to EC2...${NC}"
scp -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 run_remote_comparative_backtest.sh ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/run_comparative_backtest.sh

# Make the script executable
ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "chmod +x /home/ec2-user/aGENtrader/run_comparative_backtest.sh"

echo -e "${GREEN}Ready to run comparative backtest!${NC}"
echo -e "${YELLOW}To execute the backtest on EC2:${NC}"
echo -e "ssh -i ec2_ssh_key.pem ec2-user@\$EC2_PUBLIC_IP \"/home/ec2-user/aGENtrader/run_comparative_backtest.sh\""
echo -e "\n${YELLOW}To download the results after completion:${NC}"
echo -e "scp -r -i ec2_ssh_key.pem ec2-user@\$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/$OUTPUT_DIR ."

echo -e "\n${GREEN}Done!${NC}"
