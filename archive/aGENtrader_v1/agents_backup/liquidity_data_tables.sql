-- Liquidity Data Extensions
-- This script creates the necessary database tables for liquidity analysis

-- Table for exchange flows data
CREATE TABLE IF NOT EXISTS exchange_flows (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    symbol TEXT NOT NULL, 
    exchange TEXT NOT NULL,
    inflow NUMERIC NOT NULL,
    outflow NUMERIC NOT NULL,
    net_flow NUMERIC NOT NULL,
    interval TEXT NOT NULL,
    UNIQUE(timestamp, symbol, exchange, interval)
);

-- Table for funding rates data
CREATE TABLE IF NOT EXISTS funding_rates (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    funding_rate NUMERIC NOT NULL,
    next_funding_time TIMESTAMP,
    predicted_rate NUMERIC,
    interval TEXT NOT NULL,
    UNIQUE(timestamp, symbol, exchange, interval)
);

-- Table for order book market depth data
CREATE TABLE IF NOT EXISTS market_depth (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    depth_level NUMERIC NOT NULL,
    bid_depth NUMERIC NOT NULL,
    ask_depth NUMERIC NOT NULL,
    bid_ask_ratio NUMERIC NOT NULL,
    interval TEXT NOT NULL,
    UNIQUE(timestamp, symbol, exchange, depth_level, interval)
);

-- Table for futures basis data
CREATE TABLE IF NOT EXISTS futures_basis (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    contract_type TEXT NOT NULL,
    expiry_date TIMESTAMP,
    basis_points NUMERIC NOT NULL,
    annualized_basis NUMERIC NOT NULL,
    interval TEXT NOT NULL,
    UNIQUE(timestamp, symbol, exchange, contract_type, interval)
);

-- Table for volume profile data
CREATE TABLE IF NOT EXISTS volume_profile (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    price_level NUMERIC NOT NULL,
    volume NUMERIC NOT NULL,
    is_buying BOOLEAN NOT NULL,
    interval TEXT NOT NULL,
    time_period TEXT NOT NULL,
    UNIQUE(timestamp, symbol, exchange, price_level, interval, time_period)
);

-- Create indexes to speed up lookups
CREATE INDEX IF NOT EXISTS idx_exchange_flows_symbol ON exchange_flows(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_funding_rates_symbol ON funding_rates(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_market_depth_symbol ON market_depth(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_futures_basis_symbol ON futures_basis(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_volume_profile_symbol ON volume_profile(symbol, timestamp);