"""
Trading Bot Main Application

Main entry point for the trading bot platform with multi-agent architecture.
"""

import os
import json
import time
import argparse
import asyncio
import threading
from datetime import datetime

# Import agent controller
from orchestration.agent_controller import AgentController

async def main():
    """Main entry point for the trading bot"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Trading Bot Platform")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode without interactive prompts")
    parser.add_argument("--config", type=str, default="config/settings.json", help="Path to configuration file")
    args = parser.parse_args()

    # Create agent controller
    agent_controller = AgentController(config_path=args.config)

    # Initialize agents
    await agent_controller.initialize_agents()

    if args.headless:
        # Headless mode - just start the controller and wait
        agent_controller.start()
        print("Trading bot started in headless mode. Press Ctrl+C to exit.")
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            agent_controller.stop()
            print("Trading bot stopped.")
    else:
        # Interactive mode
        print("\nTrading Bot Platform - Interactive Mode")
        print("----------------------------------------")
        print("Available commands:")
        print("  status - Show agent controller status")
        print("  tasks - Show scheduled tasks status")
        print("  run cycle - Run a full agent cycle")
        print("  run [task] - Run a specific task")
        print("  portfolio - Show current portfolio status")
        print("  start - Start scheduled tasks")
        print("  stop - Stop scheduled tasks")
        print("  exit - Exit the program")
        print("----------------------------------------\n")

        running = True
        agent_started = False

        while running:
            try:
                command = input("trading-bot> ").strip().lower()

                if command == "exit":
                    if agent_started:
                        agent_controller.stop()
                    running = False

                elif command == "status":
                    status = agent_controller.get_status()
                    print(f"Running: {status['running']}")
                    print(f"Agents loaded: {', '.join(status['agents_loaded'])}")
                    print("Last run times:")
                    for agent, time in status.get('last_run', {}).items():
                        print(f"  {agent}: {time}")

                elif command == "start":
                    if agent_controller.start():
                        agent_started = True

                elif command == "stop":
                    if agent_controller.stop():
                        agent_started = False

                elif command == "run cycle":
                    print("Running agent cycle...")
                    await agent_controller.run_cycle()

                elif command.startswith("run "):
                    task = command[4:].strip()
                    print(f"Running task {task}...")
                    # Implement task running here
                    print(f"Task {task} not implemented yet.")

                elif command == "portfolio":
                    if "trade_execution" in agent_controller.agents:
                        trade_agent = agent_controller.agents["trade_execution"]
                        portfolio = trade_agent.get_portfolio_status()
                        print("\nCurrent Portfolio Status:")
                        print(f"Total Value: ${portfolio['total_value_usd']:.2f}")
                        print(f"Cash Balance: ${portfolio['cash_balance']:.2f}")
                        print("Holdings:")
                        for asset in portfolio["assets"]:
                            print(f"  {asset['asset']}: {asset['amount']} (${asset['value_usd']:.2f})")
                    else:
                        print("Trade execution agent not loaded.")

                elif command == "tasks":
                    # Show tasks status - placeholder for task scheduler
                    print("Task scheduler not implemented yet.")

                else:
                    print(f"Unknown command: {command}")

            except KeyboardInterrupt:
                print("\nInterrupted. Type 'exit' to quit.")
            except Exception as e:
                print(f"Error: {str(e)}")

        print("Trading bot exited.")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())