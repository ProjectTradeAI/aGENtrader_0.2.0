"""
API Response Schema Validation Module

This module provides tools for validating API responses against defined schemas.
It ensures data integrity and consistent structure before passing data to agents.
"""

import re
import json
import logging
import datetime
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Type

from aGENtrader_v2.utils.logger import get_logger
from aGENtrader_v2.utils.error_handler import ValidationError

# Setup logger
logger = get_logger("schema_validator")

# Type aliases for clarity
SchemaType = Dict[str, Any]
DataType = Dict[str, Any]
JsonType = Union[Dict[str, Any], List[Any], str, int, float, bool, None]

# Define basic type validators
def is_string(value: Any) -> bool:
    """Check if value is a string."""
    return isinstance(value, str)

def is_number(value: Any) -> bool:
    """Check if value is a number (int or float)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)

def is_integer(value: Any) -> bool:
    """Check if value is an integer."""
    return isinstance(value, int) and not isinstance(value, bool)

def is_float(value: Any) -> bool:
    """Check if value is a float."""
    return isinstance(value, float)

def is_boolean(value: Any) -> bool:
    """Check if value is a boolean."""
    return isinstance(value, bool)

def is_list(value: Any) -> bool:
    """Check if value is a list."""
    return isinstance(value, list)

def is_dict(value: Any) -> bool:
    """Check if value is a dictionary."""
    return isinstance(value, dict)

def is_null(value: Any) -> bool:
    """Check if value is None."""
    return value is None

def is_iso8601_timestamp(value: Any) -> bool:
    """Check if value is a valid ISO8601 timestamp string."""
    if not isinstance(value, str):
        return False
    
    # Handle CoinAPI format which includes the trailing zeroes and Z
    # Example: "2025-04-20T15:00:00.0000000Z"
    if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z$', value):
        return True
    
    # Basic ISO8601 regex pattern for other cases
    iso8601_pattern = r'^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(\.\d+)?(Z|[+-]\d{2}:\d{2})?$'
    
    if not re.match(iso8601_pattern, value):
        return False
    
    # Try to parse the timestamp
    try:
        # Remove trailing Z if present
        if value.endswith('Z'):
            value = value[:-1]
        
        # Handle timezone offset
        if '+' in value:
            value = value.split('+')[0]
        elif '-' in value and value.count('-') > 2:  # Account for date separators
            # Find the last occurrence of '-'
            last_dash = value.rindex('-')
            value = value[:last_dash]
        
        # Try parsing with different formats
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
        ]
        
        for fmt in formats:
            try:
                datetime.datetime.strptime(value, fmt)
                return True
            except ValueError:
                continue
                
        return False
    except Exception:
        return False

# Type mapping for validation
TYPE_VALIDATORS = {
    "STRING": is_string,
    "NUMBER": is_number,
    "INTEGER": is_integer,
    "FLOAT": is_float,
    "BOOLEAN": is_boolean,
    "ARRAY": is_list,
    "OBJECT": is_dict,
    "NULL": is_null,
    "ISO8601_TIMESTAMP": is_iso8601_timestamp,
}

def validate_field(field_name: str, value: Any, field_type: str) -> List[str]:
    """
    Validate a single field against its expected type.
    
    Args:
        field_name: Name of the field being validated
        value: The value to validate
        field_type: Expected type of the field
        
    Returns:
        List of error messages (empty if validation passed)
    """
    errors = []
    
    # Handle multiple allowed types (e.g., "STRING|NULL")
    allowed_types = field_type.split("|")
    
    # Check if value matches any of the allowed types
    if not any(TYPE_VALIDATORS.get(t, lambda x: False)(value) for t in allowed_types):
        # Build error message showing all allowed types
        type_names = " or ".join(allowed_types)
        errors.append(f"Field '{field_name}' expected {type_names}, got {type(value).__name__}")
    
    return errors

def validate_schema(data: Dict[str, Any], schema: Dict[str, str], 
                   ignore_extra: bool = False, 
                   partial: bool = False) -> List[str]:
    """
    Validate a data structure against a schema.
    
    Args:
        data: Data to validate
        schema: Schema to validate against
        ignore_extra: Whether to ignore extra fields in the data
        partial: Whether to allow missing fields in the data
        
    Returns:
        List of error messages (empty if validation passed)
    """
    if not isinstance(data, dict):
        return [f"Expected dictionary, got {type(data).__name__}"]
    
    errors = []
    
    # Check for required fields
    for field_name, field_type in schema.items():
        if field_name not in data:
            if not partial:
                errors.append(f"Missing required field: {field_name}")
        else:
            # Validate field
            field_errors = validate_field(field_name, data[field_name], field_type)
            errors.extend(field_errors)
    
    # Check for extra fields
    if not ignore_extra:
        extra_fields = set(data.keys()) - set(schema.keys())
        if extra_fields:
            errors.append(f"Unexpected fields: {', '.join(extra_fields)}")
    
    return errors

def validate_list_items(data_list: List[Any], item_schema: Dict[str, str],
                       ignore_extra: bool = False, 
                       partial: bool = False) -> List[str]:
    """
    Validate each item in a list against a schema.
    
    Args:
        data_list: List of items to validate
        item_schema: Schema to validate each item against
        ignore_extra: Whether to ignore extra fields in the items
        partial: Whether to allow missing fields in the items
        
    Returns:
        List of error messages (empty if validation passed)
    """
    if not isinstance(data_list, list):
        return [f"Expected list, got {type(data_list).__name__}"]
    
    errors = []
    
    # Validate each item
    for i, item in enumerate(data_list):
        item_errors = validate_schema(item, item_schema, ignore_extra, partial)
        for error in item_errors:
            errors.append(f"Item {i}: {error}")
    
    return errors

# Predefined schemas for different API responses
OHLCV_SCHEMA = {
    "time_period_start": "ISO8601_TIMESTAMP",
    "time_period_end": "ISO8601_TIMESTAMP",
    "time_open": "ISO8601_TIMESTAMP",
    "time_close": "ISO8601_TIMESTAMP",
    "price_open": "FLOAT|INTEGER",
    "price_high": "FLOAT|INTEGER",
    "price_low": "FLOAT|INTEGER",
    "price_close": "FLOAT|INTEGER",
    "volume_traded": "FLOAT|INTEGER",
    "trades_count": "INTEGER|NULL"
    # Note: symbol_id is optional in CoinAPI responses 
}

TICKER_SCHEMA = {
    "symbol_id": "STRING",
    "time": "ISO8601_TIMESTAMP",
    "price": "FLOAT|INTEGER",
    "last_trade": "OBJECT|NULL",
    "volume_1h": "FLOAT|INTEGER|NULL",
    "volume_24h": "FLOAT|INTEGER|NULL",
    "price_change_pct_24h": "FLOAT|NULL"
}

ORDER_BOOK_SCHEMA = {
    "symbol_id": "STRING",
    "time_exchange": "ISO8601_TIMESTAMP", 
    "time_coinapi": "ISO8601_TIMESTAMP",
    "asks": "ARRAY",
    "bids": "ARRAY"
}

# Standard market event schema
MARKET_EVENT_SCHEMA = {
    "type": "STRING",
    "symbol": "STRING",
    "timestamp": "STRING|ISO8601_TIMESTAMP",
    "ticker": "OBJECT|NULL",
    "ohlcv": "OBJECT|NULL",
    "orderbook": "OBJECT|NULL"
}

# Schema registry to lookup schemas by name
SCHEMA_REGISTRY = {
    "ohlcv": OHLCV_SCHEMA,
    "ticker": TICKER_SCHEMA,
    "orderbook": ORDER_BOOK_SCHEMA,
    "market_event": MARKET_EVENT_SCHEMA,
}

def get_schema(schema_name: str) -> Dict[str, str]:
    """
    Get a schema by name from the registry.
    
    Args:
        schema_name: Name of the schema to retrieve
        
    Returns:
        The schema dictionary
        
    Raises:
        ValueError: If schema name is unknown
    """
    if schema_name not in SCHEMA_REGISTRY:
        raise ValueError(f"Unknown schema: {schema_name}")
    
    return SCHEMA_REGISTRY[schema_name]

def validate_api_response(response_data: Any, schema_name: str,
                         ignore_extra: bool = False,
                         partial: bool = False) -> None:
    """
    Validate an API response against a named schema.
    
    Args:
        response_data: The API response data to validate
        schema_name: The name of the schema to validate against
        ignore_extra: Whether to ignore extra fields
        partial: Whether to allow missing fields
        
    Raises:
        ValidationError: If validation fails
    """
    schema = get_schema(schema_name)
    
    if isinstance(response_data, list):
        errors = validate_list_items(response_data, schema, ignore_extra, partial)
    else:
        errors = validate_schema(response_data, schema, ignore_extra, partial)
    
    if errors:
        error_message = f"API response validation failed for schema '{schema_name}':\n" + "\n".join(errors)
        logger.error(error_message)
        raise ValidationError(error_message)

def validate_market_event(event: Dict[str, Any]) -> None:
    """
    Validate a complete market event with nested components.
    
    Args:
        event: The market event to validate
        
    Raises:
        ValidationError: If validation fails
    """
    # First validate the overall structure
    errors = validate_schema(event, MARKET_EVENT_SCHEMA, ignore_extra=True, partial=False)
    
    if errors:
        error_message = "Market event validation failed:\n" + "\n".join(errors)
        logger.error(error_message)
        raise ValidationError(error_message)
    
    # Validate nested components if present
    if event.get("ticker") and is_dict(event["ticker"]):
        ticker_errors = validate_schema(event["ticker"], TICKER_SCHEMA, ignore_extra=True, partial=True)
        if ticker_errors:
            errors.append("Ticker validation failed:\n" + "\n".join(ticker_errors))
    
    if event.get("ohlcv") and is_dict(event["ohlcv"]):
        ohlcv_errors = validate_schema(event["ohlcv"], OHLCV_SCHEMA, ignore_extra=True, partial=True)
        if ohlcv_errors:
            errors.append("OHLCV validation failed:\n" + "\n".join(ohlcv_errors))
    
    if event.get("orderbook") and is_dict(event["orderbook"]):
        orderbook_errors = validate_schema(event["orderbook"], ORDER_BOOK_SCHEMA, ignore_extra=True, partial=True)
        if orderbook_errors:
            errors.append("Orderbook validation failed:\n" + "\n".join(orderbook_errors))
    
    # Check for any validation errors in nested components
    if errors:
        error_message = "Market event nested component validation failed:\n" + "\n".join(errors)
        logger.error(error_message)
        raise ValidationError(error_message)
    
    logger.debug(f"Market event validation passed for {event.get('symbol')}")