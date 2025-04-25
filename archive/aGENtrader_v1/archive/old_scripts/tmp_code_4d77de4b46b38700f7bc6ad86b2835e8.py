# Step 1
from agents.database_retrieval_tool import get_db_tool
db_tool = get_db_tool()
price_data = db_tool.get_latest_price("BTCUSDT")

# Step 2
print("Raw price data:")
print(price_data)

# Step 3
from agents.database_retrieval_tool import serialize_results
serialized_data = serialize_results(price_data)

# Step 4
print("\nSerialized price data:")
print(serialized_data)

# Step 5
market_summary = db_tool.get_market_summary("BTCUSDT")
serialized_summary = serialize_results(market_summary)

# Step 6
# Serialization is important when working with database results because it allows for the conversion of complex data structures (like dictionary or objects) into a format (like JSON) that can be easily stored, transmitted, and shared across different systems or applications.