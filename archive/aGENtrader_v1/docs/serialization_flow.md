# Database to AutoGen Serialization Flow

## System Architecture

```
┌───────────────────────┐      ┌───────────────────────┐      ┌───────────────────────┐
│                       │      │                       │      │                       │
│    SQL Database       │      │  Database Retrieval   │      │  AutoGen Integration  │
│    (Market Data)      │─────▶│        Tool           │─────▶│       Layer           │
│                       │      │                       │      │                       │
└───────────────────────┘      └───────────────────────┘      └───────────────────────┘
                                          │                              │
                                          │                              │
                                          ▼                              ▼
                               ┌───────────────────────┐      ┌───────────────────────┐
                               │                       │      │                       │
                               │   Serialization       │      │     AutoGen Agents    │
                               │      System           │─────▶│                       │
                               │                       │      │                       │
                               └───────────────────────┘      └───────────────────────┘
```

## Serialization Process

```
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│  Complex Objects  │     │  CustomJSONEncoder │     │  JSON Compatible  │
│                   │     │                    │     │                   │
│ - datetime        │────▶│ - datetime → ISO  │────▶│ - string (ISO)    │
│ - Decimal         │     │ - Decimal → float │     │ - float           │
│ - Nested Dict     │     │ - recursive       │     │ - Nested Dict     │
└───────────────────┘     └───────────────────┘     └───────────────────┘
```

## Data Flow from Database to Agent

```
┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────┐
│ Database│    │ SQL Query   │    │Raw Result   │    │Serialized    │    │ AutoGen │
│ (PG/SQL)│───▶│ Execution   │───▶│ with complex│───▶│ JSON         │───▶│ Agent   │
│         │    │             │    │ types       │    │              │    │         │
└─────────┘    └─────────────┘    └─────────────┘    └──────────────┘    └─────────┘
                                                             │
                                                             │
                                                     ┌───────────────┐
                                                     │CustomJSONEncoder│
                                                     │serialize_results│
                                                     └───────────────┘
```

## Function Registration

```
┌─────────────────────────────────────────┐
│              function_map               │
├─────────────────────────────────────────┤
│ "get_latest_price": get_latest_price    │
│ "get_price_history": get_price_history  │
│ "get_technical_indicators": get_tech... │
│ "serialize_results": serialize_results  │◄─────┐
└─────────────────────────────────────────┘      │
                      │                           │
                      ▼                           │
┌─────────────────────────────────────────┐      │
│            AssistantAgent               │      │
├─────────────────────────────────────────┤      │
│ name: "market_analyst"                  │      │
│ llm_config: {                           │      │
│   config_list: [...],                   │      │
│   function_map: function_map            │      │
│ }                                       │      │
└─────────────────────────────────────────┘      │
                      │                           │
                      ▼                           │
┌─────────────────────────────────────────┐      │
│       Agent Function Execution          │      │
├─────────────────────────────────────────┤      │
│ 1. Call Database Function               │      │
│    (returns complex types)              │      │
│ 2. Call serialize_results ─────────────────────┘
│    (converts to JSON)                   │
│ 3. Process serialized data              │
└─────────────────────────────────────────┘
```

## Database Schema Integration

```
┌───────────────────────────────────────────────────────────┐
│                     market_data                           │
├─────────────┬─────────────┬────────────┬─────────────────┤
│ symbol      │ timestamp   │ price      │ volume          │
│ VARCHAR     │ TIMESTAMP   │ DECIMAL    │ DECIMAL         │
└─────────────┴─────────────┴────────────┴─────────────────┘
                                │
                                │ Query Results
                                ▼
┌───────────────────────────────────────────────────────────┐
│                  Raw Query Result                         │
├─────────────┬─────────────┬────────────┬─────────────────┤
│ symbol      │ timestamp   │ price      │ volume          │
│ str         │ datetime    │ Decimal    │ Decimal         │
└─────────────┴─────────────┴────────────┴─────────────────┘
                                │
                                │ CustomJSONEncoder
                                ▼
┌───────────────────────────────────────────────────────────┐
│                 Serialized JSON                           │
├─────────────┬─────────────┬────────────┬─────────────────┤
│ symbol      │ timestamp   │ price      │ volume          │
│ string      │ string(ISO) │ float      │ float           │
└─────────────┴─────────────┴────────────┴─────────────────┘
```

## Example Data Transformation

### Original Data (with complex types)
```python
{
  "symbol": "BTCUSDT",
  "timestamp": datetime(2025, 3, 25, 19, 49, 29, 208083),
  "price": Decimal("87245.38"),
  "volume": Decimal("1532.45")
}
```

### After Serialization
```json
{
  "symbol": "BTCUSDT",
  "timestamp": "2025-03-25T19:49:29.208083",
  "price": 87245.38,
  "volume": 1532.45
}
```

## Integration Workflow

1. **Database Query** → Market data stored in PostgreSQL/SQL with TIMESTAMP and DECIMAL types
2. **Query Execution** → Database retrieval tool executes query and fetches results
3. **Type Conversion** → CustomJSONEncoder converts datetime and Decimal objects
4. **JSON Serialization** → serialize_results function creates formatted JSON
5. **Agent Function** → AutoGen agent receives and processes the JSON data
6. **Analysis & Decision** → Agent analyzes the data and provides insights