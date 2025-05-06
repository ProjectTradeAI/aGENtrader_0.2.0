#!/usr/bin/env python3
"""
aGENtrader v2 ToneAgent Integration Test

This script tests the integration of ToneAgent with the test harness to ensure
that agent voices are properly styled and displayed in the test output.
"""

import os
import sys
import logging
import argparse
import colorama
from colorama import Fore, Style
from datetime import datetime

# Initialize colorama
colorama.init(autoreset=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import test harness components
from tests.test_harness import AgentTestHarness

def print_banner(text, width=80, char='='):
    """Print a centered banner with the given text."""
    padding = char * ((width - len(text) - 2) // 2)
    banner = f"{padding} {text} {padding}"
    if len(banner) < width:
        banner += char  # Ensure the banner is exactly width characters
    print(f"\n{banner}\n")

def test_tone_agent_integration():
    """Test ToneAgent integration with the test harness."""
    print_banner("TESTING TONE AGENT INTEGRATION", char='*')
    
    # Create test harness for a full cycle test with TechnicalAnalystAgent
    harness = AgentTestHarness(
        agent_name="TechnicalAnalystAgent",
        symbol="BTC/USDT",
        interval="1h",
        use_mock_data=True,
        temperature=0.7,  # Higher temperature for more varied tones
        explain=True
    )
    
    # Set up full cycle mode to generate a complete decision
    harness.full_cycle = True
    
    # Run the test
    print(f"{Fore.CYAN}Running full trade cycle test with ToneAgent integration...{Style.RESET_ALL}")
    result = harness.run_test()
    
    # Check for ToneAgent output
    if 'result' in result and 'tone_summary' in result['result']:
        tone_summary = result['result']['tone_summary']
        agent_comments = tone_summary.get('agent_comments', {})
        
        if agent_comments:
            print(f"{Fore.GREEN}Success! ToneAgent generated {len(agent_comments)} agent voices.{Style.RESET_ALL}")
            
            # Display agent voices
            print_banner("AGENT VOICES", char='-')
            for agent_name, comment in agent_comments.items():
                print(f"{Fore.CYAN}{agent_name}:{Style.RESET_ALL}")
                print(f'  "{comment}"\n')
                
            # Display system summary if available
            if 'system_summary' in tone_summary:
                print_banner("SYSTEM SUMMARY", char='-')
                print(tone_summary['system_summary'])
            
            return True
        else:
            print(f"{Fore.RED}Test failed! ToneAgent did not generate any agent voices.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Test failed! ToneAgent output not found in results.{Style.RESET_ALL}")
    
    return False

def main():
    """Run tests for ToneAgent integration."""
    parser = argparse.ArgumentParser(description="Test ToneAgent integration")
    parser.add_argument('--symbol', default='BTC/USDT', help='Trading symbol to use for test')
    parser.add_argument('--interval', default='1h', help='Trading interval to use for test')
    args = parser.parse_args()
    
    # Print test configuration
    print(f"{Fore.CYAN}Testing ToneAgent integration with {args.symbol} ({args.interval}){Style.RESET_ALL}")
    
    # Run the integration test
    success = test_tone_agent_integration()
    
    # Print final result
    if success:
        print(f"\n{Fore.GREEN}✓ ToneAgent integration test completed successfully!{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}✗ ToneAgent integration test failed!{Style.RESET_ALL}")
    
if __name__ == "__main__":
    main()