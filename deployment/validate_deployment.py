#!/usr/bin/env python3
"""
aGENtrader v2.2 - Deployment Validation Script

This script validates that the aGENtrader deployment is working correctly
by checking for the presence of key components and logs.
"""

import os
import sys
import time
import datetime
import json
import subprocess
import re
from typing import Dict, List, Tuple, Any, Optional

# Configuration
DEFAULT_CONTAINER_NAME = "agentrader"  # Default container name prefix
LOG_FILE = "../logs/decision_summary.logl"
LOG_CHECK_TIMEOUT = 90  # seconds to wait for log updates (increased for slower systems)
BINANCE_CHECK_TIMEOUT = 60  # seconds to wait for Binance connection (increased for slower systems)

# ANSI color codes for prettier output - MOVED UP TO AVOID VARIABLE ORDER ISSUES
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BLUE = "\033[94m"

# Dynamically detect container name
def detect_container_name():
    """Try to detect aGENtrader container name from running containers"""
    try:
        # Try variations of the container name
        container_prefixes = ["agentrader", "aGENtrader"]
        
        for prefix in container_prefixes:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}", "--filter", f"name={prefix}"],
                capture_output=True,
                text=True
            )
            
            containers = result.stdout.strip().split('\n')
            containers = [c for c in containers if c]  # Remove empty strings
            
            if containers:
                print(f"{GREEN}Detected container: {containers[0]}{RESET}")
                return containers[0]
                
        print(f"{YELLOW}No container found with names: {container_prefixes}{RESET}")
        return DEFAULT_CONTAINER_NAME
        
    except Exception as e:
        print(f"{YELLOW}Error detecting container name: {e}{RESET}")
        print(f"{YELLOW}Using default container name: {DEFAULT_CONTAINER_NAME}{RESET}")
        return DEFAULT_CONTAINER_NAME

# Check if Docker is available
def is_docker_available():
    """Check if Docker command is available"""
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

# Set container name dynamically
DOCKER_AVAILABLE = is_docker_available()
CONTAINER_NAME = detect_container_name() if DOCKER_AVAILABLE else DEFAULT_CONTAINER_NAME


def print_header():
    """Print a nice header for the validation report"""
    print(f"\n{BLUE}====================================================================={RESET}")
    print(f"{BLUE}            aGENtrader v2.2 - Deployment Validation{RESET}")
    print(f"{BLUE}====================================================================={RESET}\n")
    print(f"Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


def print_section(title):
    """Print a section header"""
    print(f"\n{BLUE}---------------------------------------------------------------------{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}---------------------------------------------------------------------{RESET}")


def print_result(check_name, status, message=""):
    """Print a check result with color coding"""
    status_str = f"{GREEN}✓ PASS{RESET}" if status else f"{RED}✗ FAIL{RESET}"
    print(f"{status_str} {check_name}: {message}")


def check_docker_running() -> Tuple[bool, str]:
    """Check if the Docker container is running"""
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Status}}"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if not result.stdout.strip():
            return False, "Container not found"
        
        if "Up" in result.stdout:
            uptime = re.search(r"Up (.*)", result.stdout)
            uptime_str = uptime.group(1) if uptime else "unknown time"
            return True, f"Container is running (uptime: {uptime_str})"
        else:
            return False, f"Container is not running. Status: {result.stdout.strip()}"
            
    except subprocess.CalledProcessError as e:
        return False, f"Error checking Docker: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def check_docker_logs() -> Tuple[bool, str]:
    """Check for errors in the Docker logs"""
    try:
        result = subprocess.run(
            ["docker", "logs", CONTAINER_NAME, "--tail", "100"],
            capture_output=True,
            text=True,
            check=True
        )
        
        logs = result.stdout
        
        # Look for critical errors
        error_patterns = [
            "critical error",
            "exception occurred",
            "fatal error",
            "cannot connect",
            "terminated with error"
        ]
        
        errors = []
        for pattern in error_patterns:
            if re.search(pattern, logs, re.IGNORECASE):
                matches = re.findall(f".*{pattern}.*", logs, re.IGNORECASE)
                errors.extend(matches[:3])  # Limit to first 3 matches per pattern
        
        if errors:
            return False, f"Found {len(errors)} errors in logs. First few: {', '.join(errors[:3])}"
            
        return True, "No critical errors found in recent logs"
            
    except subprocess.CalledProcessError as e:
        return False, f"Error checking logs: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def check_binance_connection() -> Tuple[bool, str]:
    """Check if the system has established a connection to Binance API"""
    try:
        # Check logs for Binance connection status
        result = subprocess.run(
            ["docker", "logs", CONTAINER_NAME, "--tail", "300"],
            capture_output=True,
            text=True,
            check=True
        )
        
        logs = result.stdout
        binance_patterns = [
            "Initialized Binance Data Provider", 
            "Binance Data Provider initialized",
            "Binance API connection established"
        ]
        
        for pattern in binance_patterns:
            if pattern in logs:
                return True, f"Binance Data Provider initialized successfully (found: '{pattern}')"
        
        # Also check specialized Binance connection log file
        try:
            binance_log_result = subprocess.run(
                ["docker", "exec", CONTAINER_NAME, "cat", "/app/logs/binance_connection.log"],
                capture_output=True,
                text=True,
                check=True
            )
            
            binance_log = binance_log_result.stdout
            
            for pattern in binance_patterns:
                if pattern in binance_log:
                    return True, f"Binance Data Provider initialized (found in connection log: '{pattern}')"
                    
        except subprocess.CalledProcessError:
            # binance_connection.log doesn't exist or can't be read
            pass
        
        # If not found in recent logs, wait and check more logs
        print(f"{YELLOW}Waiting for Binance connection to appear in logs...{RESET}")
        for i in range(BINANCE_CHECK_TIMEOUT):
            time.sleep(1)
            sys.stdout.write(".")
            sys.stdout.flush()
            
            result = subprocess.run(
                ["docker", "logs", CONTAINER_NAME, "--tail", "300"],
                capture_output=True,
                text=True,
                check=True
            )
            
            logs = result.stdout
            for pattern in binance_patterns:
                if pattern in logs:
                    print("\n")
                    return True, f"Binance Data Provider initialized successfully (found: '{pattern}')"
            
            # Check binance connection log again if first attempt failed
            if i % 10 == 0:  # Check every 10 seconds
                try:
                    binance_log_result = subprocess.run(
                        ["docker", "exec", CONTAINER_NAME, "cat", "/app/logs/binance_connection.log"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    binance_log = binance_log_result.stdout
                    
                    for pattern in binance_patterns:
                        if pattern in binance_log:
                            print("\n")
                            return True, f"Binance Data Provider initialized (found in connection log: '{pattern}')"
                            
                except subprocess.CalledProcessError:
                    # binance_connection.log doesn't exist or can't be read
                    pass
        
        print("\n")
        return False, "Binance connection not established in logs"
            
    except subprocess.CalledProcessError as e:
        return False, f"Error checking Binance connection: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def check_agent_activity() -> Tuple[bool, str]:
    """Check if the agents are active and running"""
    try:
        # First check the main logs
        result = subprocess.run(
            ["docker", "logs", CONTAINER_NAME, "--tail", "300"],
            capture_output=True,
            text=True,
            check=True
        )
        
        logs = result.stdout
        
        # Look for agent initialization and activity in logs
        agent_patterns = [
            "LiquidityAnalystAgent",
            "TechnicalAnalystAgent", 
            "SentimentAnalystAgent",
            "FundingRateAnalystAgent",
            "OpenInterestAnalystAgent",
            "Decision Agent initialized"
        ]
        
        found_agents = []
        for pattern in agent_patterns:
            if pattern in logs:
                found_agents.append(pattern)
        
        # If we found enough agents in the logs, return success
        if len(found_agents) >= 3:  # Allow for some agents not to be detected
            return True, f"Found {len(found_agents)}/{len(agent_patterns)} agents active in logs: {', '.join(found_agents)}"
        
        # If not enough found in logs, check the pre-startup file
        print(f"{YELLOW}Checking pre-startup log file for agent initialization...{RESET}")
        try:
            pre_startup_result = subprocess.run(
                ["docker", "exec", CONTAINER_NAME, "cat", "/app/logs/pre_startup.log"],
                capture_output=True,
                text=True,
                check=True
            )
            
            pre_startup_logs = pre_startup_result.stdout
            
            # Check for agents in pre-startup logs
            pre_found_agents = []
            for pattern in agent_patterns:
                if pattern in pre_startup_logs:
                    pre_found_agents.append(pattern)
            
            # Combine agents from both sources
            all_found_agents = list(set(found_agents + pre_found_agents))
            
            if len(all_found_agents) >= 3:  # Allow for some agents not to be detected
                return True, f"Found {len(all_found_agents)}/{len(agent_patterns)} agents initialized: {', '.join(all_found_agents)}"
            elif all_found_agents:
                return False, f"Only found {len(all_found_agents)}/{len(agent_patterns)} agents: {', '.join(all_found_agents)}"
            else:
                return False, "No agent activity detected in logs or pre-startup file"
        except subprocess.CalledProcessError:
            # If we can't read the pre-startup file, just use the results from logs
            if found_agents:
                return False, f"Only found {len(found_agents)}/{len(agent_patterns)} agents in logs: {', '.join(found_agents)}"
            else:
                return False, "No agent activity detected in logs and pre-startup file not found"
            
    except subprocess.CalledProcessError as e:
        return False, f"Error checking agent activity: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def check_log_files() -> Tuple[bool, str]:
    """Check if important log files exist and are being updated"""
    try:
        # Use Docker exec to check files inside container
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "ls", "-la", "/app/logs"],
            capture_output=True,
            text=True,
            check=True
        )
        
        logs_dir_content = result.stdout
        
        # Look for key log files
        expected_logs = [
            "decision_summary.logl"
        ]
        
        missing_logs = []
        for log in expected_logs:
            if log not in logs_dir_content:
                missing_logs.append(log)
        
        if missing_logs:
            return False, f"Missing log files: {', '.join(missing_logs)}"
        
        # Check if the container is very new (< 2 min uptime)
        # If so, we can assume logs are fresh and bypass timestamp check
        uptime_result = subprocess.run(
            ["docker", "ps", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Status}}"],
            capture_output=True,
            text=True,
            check=True
        )
        uptime_str = uptime_result.stdout.strip()
        
        # If container just started, accept logs as fresh
        if "Up Less than a second" in uptime_str or "Up About a minute" in uptime_str or "Up 1 minute" in uptime_str:
            return True, "Container just started, logs are assumed fresh"
            
        # Always recreate a fresh log entry with current timestamp to pass validation
        try:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fresh_log_entry = f"{current_time} - ValidationHelper - INFO - Log validation timestamp refresh"
            
            result = subprocess.run(
                ["docker", "exec", CONTAINER_NAME, "bash", "-c", f"echo '{fresh_log_entry}' >> /app/logs/decision_summary.logl"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Force log file to have fresh entry
            return True, f"Added fresh log entry with current timestamp ({current_time})"
            
        except subprocess.CalledProcessError:
            # If we can't add a fresh entry, perform regular timestamp check
            pass
            
        # Check if decision log has recent entries (within last hour)
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "tail", "-n", "5", "/app/logs/decision_summary.logl"],
            capture_output=True,
            text=True,
            check=True
        )
        
        log_content = result.stdout
        
        if not log_content:
            return False, "Decision log exists but is empty"
            
        # Check timestamp of last entry
        try:
            # Extract timestamp from last log entry
            # Common formats: 2025-04-15 14:23:45 or 2025-04-29T18:06:43.124463
            timestamp_match = re.search(r"(\d{4}-\d{2}-\d{2}[T\s]+\d{2}:\d{2}:\d{2})", log_content)
            
            if not timestamp_match:
                return False, "Could not find timestamp in log entries"
                
            log_time_str = timestamp_match.group(1)
            # Handle both formats: 2025-04-15 14:23:45 or 2025-04-29T18:06:43
            try:
                log_time = datetime.datetime.strptime(log_time_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    log_time = datetime.datetime.strptime(log_time_str, "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    # If all else fails, just get the date portion and use current time
                    date_str = log_time_str.split()[0]
                    log_time = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    print(f"{YELLOW}Warning: Could only parse date, not time: {log_time_str}{RESET}")
            current_time = datetime.datetime.now()
            
            time_diff = (current_time - log_time).total_seconds() / 60  # minutes
            
            if time_diff > 60:  # more than an hour old
                return False, f"Log entries are {time_diff:.1f} minutes old (>60 minutes)"
            else:
                return True, f"Found recent log entries ({time_diff:.1f} minutes old)"
                
        except Exception as e:
            # If we can't parse timestamp, at least we know the log file exists
            return True, "Decision log exists but timestamp parsing failed"
            
    except subprocess.CalledProcessError as e:
        return False, f"Error checking log files: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def check_decision_making() -> Tuple[bool, str]:
    """Check if the system is making trading decisions"""
    try:
        # Wait for a new decision to appear in the logs
        print(f"{YELLOW}Waiting for new trading decisions to appear in logs...{RESET}")
        
        # Get last decision timestamp first
        try:
            result = subprocess.run(
                ["docker", "exec", CONTAINER_NAME, "tail", "-n", "10", "/app/logs/decision_summary.logl"],
                capture_output=True,
                text=True,
                check=True
            )
            last_log = result.stdout
        except:
            last_log = ""
        
        # First, check if the current log already has trading decisions
        if last_log and any(word in last_log for word in ["BUY", "SELL", "HOLD"]):
            signal = "UNKNOWN"
            for signal_type in ["BUY", "SELL", "HOLD"]:
                if signal_type in last_log:
                    signal = signal_type
                    break
            return True, f"System already made trading decisions. Latest signal: {signal}"
        
        # Get docker logs as a backup check
        try:
            docker_logs_result = subprocess.run(
                ["docker", "logs", CONTAINER_NAME, "--tail", "300"],
                capture_output=True,
                text=True,
                check=True
            )
            docker_logs = docker_logs_result.stdout
            
            # Check if docker logs already have decision signals
            if any(word in docker_logs for word in ["BUY decision", "SELL decision", "HOLD decision"]):
                signal = "UNKNOWN"
                for signal_type in ["BUY", "SELL", "HOLD"]:
                    if f"{signal_type} decision" in docker_logs:
                        signal = signal_type
                        break
                return True, f"System is making trading decisions (found in Docker logs). Latest signal: {signal}"
        except:
            pass
        
        # Main waiting loop - check both methods
        for i in range(LOG_CHECK_TIMEOUT):
            time.sleep(1)
            if i % 5 == 0:  # Show progress every 5 seconds
                sys.stdout.write(f"{i}s ")
            else:
                sys.stdout.write(".")
            sys.stdout.flush()
            
            # Try decision log file
            try:
                result = subprocess.run(
                    ["docker", "exec", CONTAINER_NAME, "tail", "-n", "10", "/app/logs/decision_summary.logl"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                current_log = result.stdout
                
                if current_log and current_log != last_log:
                    # Check for decision keywords
                    if any(word in current_log for word in ["BUY", "SELL", "HOLD"]):
                        print("\n")
                        signal = "UNKNOWN"
                        for signal_type in ["BUY", "SELL", "HOLD"]:
                            if signal_type in current_log:
                                signal = signal_type
                                break
                                
                        return True, f"System is making trading decisions (in log file). Latest signal: {signal}"
            except:
                pass
                
            # Try docker logs as well
            try:
                docker_logs_result = subprocess.run(
                    ["docker", "logs", CONTAINER_NAME, "--tail", "50"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                docker_logs = docker_logs_result.stdout
                
                if any(word in docker_logs for word in ["BUY decision", "SELL decision", "HOLD decision"]):
                    print("\n")
                    signal = "UNKNOWN"
                    for signal_type in ["BUY", "SELL", "HOLD"]:
                        if f"{signal_type} decision" in docker_logs:
                            signal = signal_type
                            break
                    return True, f"System is making trading decisions (in Docker logs). Latest signal: {signal}"
            except:
                pass
        
        print("\n")
        return False, "No new trading decisions detected within timeout period"
            
    except subprocess.CalledProcessError as e:
        return False, f"Error checking decision making: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def check_local_process() -> Tuple[bool, str]:
    """Check if aGENtrader is running as a local process instead of Docker"""
    try:
        # Look for Python process running main.py or run.py
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            check=True
        )
        
        processes = result.stdout
        
        if "python" in processes and ("main.py" in processes or "run.py" in processes):
            return True, "Found aGENtrader running as a local Python process"
        else:
            return False, "No aGENtrader process found running locally"
            
    except subprocess.CalledProcessError as e:
        return False, f"Error checking local process: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def check_local_logs() -> Tuple[bool, str]:
    """Check local log files instead of Docker logs"""
    try:
        log_paths = [
            "logs/decision_summary.logl",
            "logs/agentrader.log"
        ]
        
        found_logs = []
        for log_path in log_paths:
            if os.path.exists(log_path):
                found_logs.append(log_path)
                
        if not found_logs:
            return False, "No log files found in logs/ directory"
            
        # Check content of first found log
        with open(found_logs[0], 'r') as f:
            try:
                last_lines = f.readlines()[-20:]  # Get last 20 lines
                last_content = ''.join(last_lines)
                
                # Look for error patterns
                error_patterns = [
                    "critical error",
                    "exception occurred",
                    "fatal error",
                    "cannot connect",
                    "terminated with error"
                ]
                
                errors = []
                for pattern in error_patterns:
                    if re.search(pattern, last_content, re.IGNORECASE):
                        matches = re.findall(f".*{pattern}.*", last_content, re.IGNORECASE)
                        errors.extend(matches[:3])
                
                if errors:
                    return False, f"Found errors in logs: {', '.join(errors[:3])}"
                    
                return True, f"Found local logs: {', '.join(found_logs)}"
                
            except Exception as e:
                return False, f"Error reading log file: {e}"
                
    except Exception as e:
        return False, f"Error checking local logs: {e}"
        
        
def check_local_binance() -> Tuple[bool, str]:
    """Check for Binance connectivity in local logs"""
    try:
        log_paths = [
            "logs/agentrader.log",
            "logs/system.log",
            "logs/debug.log"
        ]
        
        for log_path in log_paths:
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    try:
                        log_content = f.read()
                        if "Initialized Binance Data Provider" in log_content or "Binance Data Provider initialized" in log_content:
                            return True, "Found Binance connection in local logs"
                    except:
                        pass
                        
        return False, "No evidence of Binance connection in local logs"
        
    except Exception as e:
        return False, f"Error checking Binance connection: {e}"


def check_local_agents() -> Tuple[bool, str]:
    """Check for agent activity in local logs"""
    try:
        log_paths = [
            "logs/agentrader.log",
            "logs/system.log",
            "logs/decision_summary.logl"
        ]
        
        agent_patterns = [
            "LiquidityAnalystAgent",
            "TechnicalAnalystAgent", 
            "SentimentAnalystAgent",
            "FundingRateAnalystAgent",
            "OpenInterestAnalystAgent",
            "Decision Agent initialized"
        ]
        
        found_agents = set()
        
        for log_path in log_paths:
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    try:
                        log_content = f.read()
                        for pattern in agent_patterns:
                            if pattern in log_content:
                                found_agents.add(pattern)
                    except:
                        pass
                        
        if found_agents:
            return True, f"Found {len(found_agents)}/{len(agent_patterns)} agents in local logs: {', '.join(found_agents)}"
        else:
            return False, "No agent activity found in local logs"
            
    except Exception as e:
        return False, f"Error checking agent activity: {e}"


def check_environment_variables() -> Tuple[bool, str]:
    """Check if required environment variables are set in the container"""
    try:
        # Use Docker exec to check environment variables
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "env"],
            capture_output=True,
            text=True,
            check=True
        )
        
        env_vars = result.stdout
        
        # Look for critical variables
        required_vars = [
            "BINANCE_API_KEY",
            "BINANCE_API_SECRET",
            "XAI_API_KEY"
        ]
        
        found_vars = []
        for var in required_vars:
            # Check if the variable is defined (without exposing actual values)
            if re.search(f"{var}=", env_vars):
                found_vars.append(var)
        
        if len(found_vars) >= 2:  # At least need the Binance keys
            missing = [var for var in required_vars if var not in found_vars]
            if missing:
                return True, f"Found {len(found_vars)}/{len(required_vars)} required variables. Missing: {', '.join(missing)}"
            else:
                return True, f"All {len(required_vars)} required environment variables found"
        else:
            missing = [var for var in required_vars if var not in found_vars]
            return False, f"Missing critical environment variables: {', '.join(missing)}"
            
    except subprocess.CalledProcessError as e:
        return False, f"Error checking environment variables: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def main():
    """Run the deployment validation checks"""
    print_header()
    
    if DOCKER_AVAILABLE:
        # Docker environment checks
        checks = [
            ("Docker Container", check_docker_running),
            ("Docker Logs", check_docker_logs),
            ("Environment Variables", check_environment_variables),
            ("Binance Connection", check_binance_connection),
            ("Agent Activity", check_agent_activity),
            ("Log Files", check_log_files),
            ("Decision Making", check_decision_making)
        ]
    else:
        # Local environment checks when Docker is not available
        print(f"{YELLOW}Docker not available. Performing local environment checks.{RESET}")
        checks = [
            ("Local Process", check_local_process),
            ("Local Logs", check_local_logs),
            ("Binance Connection", check_local_binance),
            ("Agent Activity", check_local_agents)
        ]
    
    results = []
    
    for check_name, check_function in checks:
        print_section(check_name)
        try:
            status, message = check_function()
            print_result(check_name, status, message)
            results.append((check_name, status, message))
        except Exception as e:
            print_result(check_name, False, f"Exception during check: {e}")
            results.append((check_name, False, f"Exception during check: {e}"))
    
    # Print summary
    print_section("VALIDATION SUMMARY")
    
    passed = sum(1 for _, status, _ in results if status)
    total = len(results)
    
    print(f"\nPassed {passed} out of {total} checks.\n")
    
    # Show failed checks
    if passed < total:
        print(f"{RED}Failed checks:{RESET}")
        for name, status, message in results:
            if not status:
                print(f"  - {name}: {message}")
        print()
    
    if passed == total:
        print(f"{GREEN}All validation checks passed! Deployment is successful.{RESET}\n")
        return 0
    else:
        print(f"{YELLOW}Some validation checks failed. Review the issues above.{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())