"""
Python Executor Module

This module provides utilities for executing Python code dynamically:
- Code validation and sandbox execution
- Function registration and invocation
- Result formatting and error handling
"""

import os
import sys
import json
import yaml
import logging
import inspect
import traceback
from typing import Dict, List, Any, Optional, Union, Callable
import pandas as pd
import numpy as np

# Add parent directory to path to allow importing from other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=os.path.join(parent_dir, "logs/agent_output.log")
)
logger = logging.getLogger("python_executor")

# Add console handler for debugging
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class PythonExecutor:
    """
    Python code executor that provides safe execution of code.
    
    This class:
    - Manages a sandbox environment for code execution
    - Handles code validation and security
    - Registers helper functions for common tasks
    - Formats execution results
    """
    
    def __init__(self):
        """Initialize the Python Executor."""
        self.logger = logging.getLogger("python_executor")
        
        # Initialize registry of helper functions
        self.functions = {}
        
        # Register built-in helper functions
        self._register_builtin_functions()
        
        self.logger.info("Python Executor initialized")
    
    def _register_builtin_functions(self) -> None:
        """Register built-in helper functions."""
        # Register data analysis functions
        self.register_function("calculate_sma", self._calculate_sma)
        self.register_function("calculate_ema", self._calculate_ema)
        self.register_function("calculate_rsi", self._calculate_rsi)
        self.register_function("calculate_bollinger_bands", self._calculate_bollinger_bands)
        self.register_function("find_support_resistance", self._find_support_resistance)
        
        # Register data transformation functions
        self.register_function("normalize_data", self._normalize_data)
        self.register_function("calculate_returns", self._calculate_returns)
        self.register_function("calculate_correlation", self._calculate_correlation)
        
        # Register liquidity analysis functions
        self.register_function("calculate_bid_ask_ratio", self._calculate_bid_ask_ratio)
        self.register_function("analyze_volume_profile", self._analyze_volume_profile)
        self.register_function("calculate_vwap", self._calculate_vwap)
    
    def register_function(self, name: str, func: Callable) -> None:
        """
        Register a function for use in code execution.
        
        Args:
            name: Function name to register
            func: Function to register
        """
        self.functions[name] = func
        self.logger.debug(f"Registered function: {name}")
    
    def execute_code(self, 
                   code: str, 
                   inputs: Optional[Dict[str, Any]] = None, 
                   safe_mode: bool = True) -> Dict[str, Any]:
        """
        Execute Python code with provided inputs.
        
        Args:
            code: Python code to execute
            inputs: Dictionary of input variables
            safe_mode: Whether to run in restricted mode
            
        Returns:
            Dictionary with execution results and metadata
        """
        self.logger.info("Executing Python code")
        
        # Initialize execution environment
        execution_env = {}
        
        # Add inputs to environment
        if inputs:
            execution_env.update(inputs)
        
        # Add helper functions to environment
        execution_env.update(self.functions)
        
        # Add safe imports
        safe_imports = {
            "pd": pd,
            "np": np,
            "json": json
        }
        execution_env.update(safe_imports)
        
        # Initialize result
        result = {
            "success": False,
            "output": None,
            "error": None,
            "runtime": 0,
            "code": code
        }
        
        try:
            # Basic security validation
            if safe_mode:
                self._validate_code(code)
            
            # Execute code
            import time
            start_time = time.time()
            
            # Create locals dictionary for execution
            local_vars = dict(execution_env)
            
            # Execute the code
            exec(code, {"__builtins__": __builtins__}, local_vars)
            
            # Measure execution time
            end_time = time.time()
            result["runtime"] = end_time - start_time
            
            # Extract result from 'result' variable if defined
            if "result" in local_vars:
                result["output"] = local_vars["result"]
                result["success"] = True
            else:
                # If no explicit result, return all new or modified variables
                new_vars = {k: v for k, v in local_vars.items() 
                            if k not in execution_env and not k.startswith("_")}
                result["output"] = new_vars
                result["success"] = True
        
        except Exception as e:
            self.logger.error(f"Error executing code: {e}")
            result["error"] = {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc()
            }
        
        return result
    
    def call_function(self, 
                    function_name: str, 
                    *args, 
                    **kwargs) -> Dict[str, Any]:
        """
        Call a registered function with provided arguments.
        
        Args:
            function_name: Name of function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Dictionary with function result and metadata
        """
        self.logger.info(f"Calling function: {function_name}")
        
        # Initialize result
        result = {
            "success": False,
            "output": None,
            "error": None,
            "function": function_name,
            "args": args,
            "kwargs": kwargs
        }
        
        # Check if function exists
        if function_name not in self.functions:
            result["error"] = {
                "type": "FunctionNotFound",
                "message": f"Function '{function_name}' not found in registry"
            }
            return result
        
        try:
            # Call function
            func = self.functions[function_name]
            output = func(*args, **kwargs)
            
            # Set result
            result["output"] = output
            result["success"] = True
        
        except Exception as e:
            self.logger.error(f"Error calling function '{function_name}': {e}")
            result["error"] = {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc()
            }
        
        return result
    
    def _validate_code(self, code: str) -> None:
        """
        Validate code for security concerns.
        
        Args:
            code: Python code to validate
            
        Raises:
            ValueError: If code contains prohibited keywords
        """
        # List of prohibited operations
        prohibited = [
            "import os",
            "import subprocess",
            "import sys",
            "__import__",
            "eval(",
            "exec(",
            "open(",
            "file(",
            "globals(",
            "locals(",
            "compile(",
            "__builtins__"
        ]
        
        # Check for prohibited operations
        for item in prohibited:
            if item in code:
                raise ValueError(f"Prohibited operation detected: {item}")
    
    # Built-in helper functions for data analysis
    
    def _calculate_sma(self, data: Union[pd.DataFrame, pd.Series, List[float]], window: int) -> Union[pd.Series, List[float]]:
        """Calculate Simple Moving Average."""
        if isinstance(data, pd.DataFrame):
            return data.rolling(window=window).mean()
        elif isinstance(data, pd.Series):
            return data.rolling(window=window).mean()
        else:
            # Convert list to pandas Series
            series = pd.Series(data)
            return series.rolling(window=window).mean().tolist()
    
    def _calculate_ema(self, data: Union[pd.DataFrame, pd.Series, List[float]], window: int) -> Union[pd.Series, List[float]]:
        """Calculate Exponential Moving Average."""
        if isinstance(data, pd.DataFrame):
            return data.ewm(span=window, adjust=False).mean()
        elif isinstance(data, pd.Series):
            return data.ewm(span=window, adjust=False).mean()
        else:
            # Convert list to pandas Series
            series = pd.Series(data)
            return series.ewm(span=window, adjust=False).mean().tolist()
    
    def _calculate_rsi(self, data: Union[pd.Series, List[float]], window: int = 14) -> Union[pd.Series, List[float]]:
        """Calculate Relative Strength Index."""
        if not isinstance(data, pd.Series):
            data = pd.Series(data)
        
        # Calculate price changes
        delta = data.diff()
        
        # Separate gains and losses
        gain = delta.copy()
        loss = delta.copy()
        gain[gain < 0] = 0
        loss[loss > 0] = 0
        loss = -loss  # Make losses positive
        
        # Calculate average gain and loss
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.tolist() if not isinstance(data, pd.Series) else rsi
    
    def _calculate_bollinger_bands(self, 
                               data: Union[pd.Series, List[float]], 
                               window: int = 20, 
                               num_std: float = 2.0) -> Dict[str, Union[pd.Series, List[float]]]:
        """Calculate Bollinger Bands."""
        if not isinstance(data, pd.Series):
            data = pd.Series(data)
        
        # Calculate SMA
        sma = data.rolling(window=window).mean()
        
        # Calculate standard deviation
        std = data.rolling(window=window).std()
        
        # Calculate upper and lower bands
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        
        if not isinstance(data, pd.Series):
            return {
                "middle": sma.tolist(),
                "upper": upper_band.tolist(),
                "lower": lower_band.tolist()
            }
        else:
            return {
                "middle": sma,
                "upper": upper_band,
                "lower": lower_band
            }
    
    def _find_support_resistance(self, 
                              data: Union[pd.DataFrame, List[Dict[str, float]]], 
                              window: int = 10,
                              threshold: float = 0.01) -> Dict[str, List[float]]:
        """Find support and resistance levels."""
        # Convert to DataFrame if list of dicts
        if isinstance(data, list):
            data = pd.DataFrame(data)
        
        # Ensure we have high and low columns
        if not all(col in data.columns for col in ["high", "low"]):
            raise ValueError("Data must contain 'high' and 'low' columns")
        
        highs = data["high"].values
        lows = data["low"].values
        
        # Find local maxima and minima
        resistance_levels = []
        support_levels = []
        
        for i in range(window, len(data) - window):
            # Check if this is a local maximum
            if highs[i] == max(highs[i-window:i+window+1]):
                resistance_levels.append(highs[i])
            
            # Check if this is a local minimum
            if lows[i] == min(lows[i-window:i+window+1]):
                support_levels.append(lows[i])
        
        # Filter out levels that are too close to each other
        filtered_resistance = []
        for r in resistance_levels:
            if not filtered_resistance or min(abs((r - fr) / fr) for fr in filtered_resistance) > threshold:
                filtered_resistance.append(r)
        
        filtered_support = []
        for s in support_levels:
            if not filtered_support or min(abs((s - fs) / fs) for fs in filtered_support) > threshold:
                filtered_support.append(s)
        
        return {
            "support": sorted(filtered_support),
            "resistance": sorted(filtered_resistance)
        }
    
    def _normalize_data(self, data: Union[pd.DataFrame, pd.Series, List[float]], method: str = "minmax") -> Union[pd.DataFrame, pd.Series, List[float]]:
        """Normalize data using specified method."""
        if isinstance(data, list):
            data = pd.Series(data)
        
        if method == "minmax":
            # Min-max normalization
            if isinstance(data, pd.DataFrame):
                return (data - data.min()) / (data.max() - data.min())
            else:
                return (data - data.min()) / (data.max() - data.min())
        
        elif method == "zscore":
            # Z-score normalization
            if isinstance(data, pd.DataFrame):
                return (data - data.mean()) / data.std()
            else:
                return (data - data.mean()) / data.std()
        
        else:
            raise ValueError(f"Unknown normalization method: {method}")
    
    def _calculate_returns(self, 
                        prices: Union[pd.Series, List[float]], 
                        period: int = 1,
                        log_returns: bool = False) -> Union[pd.Series, List[float]]:
        """Calculate price returns."""
        if isinstance(prices, list):
            prices = pd.Series(prices)
        
        if log_returns:
            returns = np.log(prices / prices.shift(period))
        else:
            returns = prices.pct_change(period)
        
        return returns.tolist() if isinstance(prices, list) else returns
    
    def _calculate_correlation(self, 
                            series1: Union[pd.Series, List[float]], 
                            series2: Union[pd.Series, List[float]],
                            method: str = "pearson") -> float:
        """Calculate correlation between two series."""
        if isinstance(series1, list):
            series1 = pd.Series(series1)
        
        if isinstance(series2, list):
            series2 = pd.Series(series2)
        
        return series1.corr(series2, method=method)
    
    def _calculate_bid_ask_ratio(self, 
                              bid_volumes: Union[pd.Series, List[float]], 
                              ask_volumes: Union[pd.Series, List[float]]) -> Union[pd.Series, List[float]]:
        """Calculate bid/ask volume ratio."""
        if isinstance(bid_volumes, list):
            bid_volumes = pd.Series(bid_volumes)
        
        if isinstance(ask_volumes, list):
            ask_volumes = pd.Series(ask_volumes)
        
        ratio = bid_volumes / ask_volumes
        
        return ratio.tolist() if isinstance(bid_volumes, list) else ratio
    
    def _analyze_volume_profile(self, 
                             prices: Union[pd.Series, List[float]], 
                             volumes: Union[pd.Series, List[float]],
                             num_bins: int = 10) -> Dict[str, Any]:
        """Analyze volume distribution by price level."""
        if isinstance(prices, list):
            prices = pd.Series(prices)
        
        if isinstance(volumes, list):
            volumes = pd.Series(volumes)
        
        # Create DataFrame with price and volume
        df = pd.DataFrame({"price": prices, "volume": volumes})
        
        # Create price bins
        min_price = df["price"].min()
        max_price = df["price"].max()
        bin_width = (max_price - min_price) / num_bins
        
        df["price_bin"] = ((df["price"] - min_price) / bin_width).astype(int)
        df["price_bin"] = df["price_bin"].clip(upper=num_bins-1)
        
        # Calculate volume profile
        volume_profile = df.groupby("price_bin").agg({
            "volume": "sum",
            "price": "mean"
        }).reset_index()
        
        # Find POC (Point of Control) - price level with highest volume
        poc_row = volume_profile.loc[volume_profile["volume"].idxmax()]
        poc = {
            "price": float(poc_row["price"]),
            "volume": float(poc_row["volume"])
        }
        
        # Calculate value area (70% of volume)
        total_volume = volume_profile["volume"].sum()
        value_area_target = total_volume * 0.7
        
        # Sort by volume descending
        sorted_profile = volume_profile.sort_values("volume", ascending=False)
        cumulative_volume = 0
        value_area_levels = []
        
        for _, row in sorted_profile.iterrows():
            cumulative_volume += row["volume"]
            value_area_levels.append(float(row["price"]))
            if cumulative_volume >= value_area_target:
                break
        
        # Get value area high and low
        value_area_high = max(value_area_levels)
        value_area_low = min(value_area_levels)
        
        return {
            "volume_profile": volume_profile.to_dict(orient="records"),
            "poc": poc,
            "value_area_high": value_area_high,
            "value_area_low": value_area_low,
            "bin_width": bin_width
        }
    
    def _calculate_vwap(self, 
                      df: pd.DataFrame, 
                      price_col: str = "close", 
                      volume_col: str = "volume") -> pd.Series:
        """Calculate Volume Weighted Average Price."""
        if isinstance(df, list):
            df = pd.DataFrame(df)
        
        df = df.copy()
        df["pv"] = df[price_col] * df[volume_col]
        df["cumulative_pv"] = df["pv"].cumsum()
        df["cumulative_volume"] = df[volume_col].cumsum()
        df["vwap"] = df["cumulative_pv"] / df["cumulative_volume"]
        
        return df["vwap"]

# Example usage (for demonstration)
if __name__ == "__main__":
    # Create executor
    executor = PythonExecutor()
    
    # Example code to execute
    test_code = """
    # Simple code to analyze market data
    prices = [100, 102, 104, 103, 105, 107, 108, 107, 106, 105]
    volumes = [100, 150, 200, 120, 180, 190, 210, 150, 120, 100]
    
    # Calculate indicators
    sma_5 = calculate_sma(prices, 5)
    rsi_7 = calculate_rsi(prices, 7)
    
    # Analyze volume profile
    volume_analysis = analyze_volume_profile(prices, volumes, 5)
    
    # Assemble result
    result = {
        "sma_5": sma_5,
        "rsi_7": rsi_7,
        "volume_analysis": volume_analysis
    }
    """
    
    # Execute code
    result = executor.execute_code(test_code)
    
    # Print result
    if result["success"]:
        print("Code executed successfully")
        print(f"Result: {json.dumps(result['output'], indent=2)}")
    else:
        print("Error executing code:")
        print(result["error"]["message"])