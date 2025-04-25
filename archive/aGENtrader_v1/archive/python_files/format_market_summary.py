def _format_market_summary(self, market_data):
    """
    Format market data as a human-readable summary for the initial message.
    
    Args:
        market_data: Market data dictionary
        
    Returns:
        Formatted market summary text
    """
    if not market_data:
        return "No market data available."
    
    summary_parts = ["## Market Summary"]
    
    # Extract summary info if available
    if "market_summary" in market_data and market_data["market_summary"]:
        ms = market_data["market_summary"]
        summary_parts.append(f"- Price Change: {ms.get('percent_change', 0):.2f}%")
        summary_parts.append(f"- Market Condition: {ms.get('market_condition', 'unknown')}")
    
    # Add technical indicators
    if "technical_indicators" in market_data:
        ti = market_data["technical_indicators"]
        summary_parts.append("\n## Technical Indicators")
        
        if ti.get("rsi") and "rsi" in ti["rsi"]:
            rsi_value = ti["rsi"]["rsi"]
            rsi_interp = ti["rsi"].get("interpretation", "")
            summary_parts.append(f"- RSI: {rsi_value:.2f} ({rsi_interp})")
        
        if ti.get("sma") and "moving_average" in ti["sma"]:
            sma_value = ti["sma"]["moving_average"]
            current_price = market_data.get("latest_price", {}).get("close", 0)
            if current_price and sma_value:
                relation = "above" if current_price > sma_value else "below"
                summary_parts.append(f"- SMA: {sma_value:.2f} (price is {relation} SMA)")
        
        # Add support/resistance
        if ti.get("support_resistance"):
            sr = ti["support_resistance"]
            if "support_levels" in sr and sr["support_levels"]:
                supports = ", ".join([f"${s:.2f}" for s in sr["support_levels"][:2]])
                summary_parts.append(f"- Support Levels: {supports}")
            if "resistance_levels" in sr and sr["resistance_levels"]:
                resistances = ", ".join([f"${r:.2f}" for r in sr["resistance_levels"][:2]])
                summary_parts.append(f"- Resistance Levels: {resistances}")
        
        # Add patterns if detected
        if ti.get("patterns") and "patterns" in ti["patterns"]:
            patterns = ti["patterns"]["patterns"]
            if patterns:
                pattern_names = ", ".join([p["name"] for p in patterns])
                summary_parts.append(f"- Detected Patterns: {pattern_names}")
            else:
                summary_parts.append("- No significant patterns detected")
        
        # Add volatility
        if ti.get("volatility"):
            vol = ti["volatility"]
            if "volatility" in vol:
                vol_value = vol["volatility"]
                vol_interp = vol.get("interpretation", "")
                summary_parts.append(f"- Volatility: {vol_value:.4f} ({vol_interp})")
                
    # Add global market overview if available
    if "global_market" in market_data:
        gm = market_data["global_market"]
        summary_parts.append("\n## Global Market Overview")
        
        # Add crypto market metrics
        if "crypto_metrics" in gm and gm["crypto_metrics"]:
            cm = gm["crypto_metrics"]
            if "market_cap" in cm:
                summary_parts.append(f"- Total Crypto Market Cap: ${cm.get('market_cap', 0)/1e9:.2f}B")
            if "btc_dominance" in cm:
                summary_parts.append(f"- BTC Dominance: {cm.get('btc_dominance', 0):.2f}%")
        
        # Add market indices
        if "market_indices" in gm and gm["market_indices"]:
            indices = gm["market_indices"]
            if "dxy" in indices:
                dxy = indices.get("dxy", {})
                dxy_value = dxy.get("value")
                dxy_change = dxy.get("change")
                if dxy_value and dxy_change is not None:
                    direction = "up" if dxy_change > 0 else "down"
                    summary_parts.append(f"- DXY: {dxy_value:.2f} ({direction} {abs(dxy_change):.2f}%)")
        
        # Add correlations
        if "correlations" in gm and gm["correlations"]:
            correlations = gm["correlations"]
            corr_list = []
            if "sp500" in correlations:
                corr_list.append(f"S&P 500: {correlations['sp500']:.2f}")
            if "gold" in correlations:
                corr_list.append(f"Gold: {correlations['gold']:.2f}")
            if "dxy" in correlations:
                corr_list.append(f"DXY: {correlations['dxy']:.2f}")
            
            if corr_list:
                summary_parts.append(f"- Correlations: {', '.join(corr_list)}")
            
    # Add liquidity overview if available
    if "liquidity" in market_data:
        liq = market_data["liquidity"]
        summary_parts.append("\n## Liquidity Overview")
        
        # Add exchange flows
        if "exchange_flows" in liq and liq["exchange_flows"]:
            ef = liq["exchange_flows"]
            if "net_flow" in ef:
                net_flow = ef["net_flow"]
                flow_direction = "inflow" if net_flow > 0 else "outflow"
                summary_parts.append(f"- Exchange Flows: Net {flow_direction} of {abs(net_flow):.2f} BTC")
        
        # Add funding rates
        if "funding_rates" in liq and liq["funding_rates"]:
            fr = liq["funding_rates"]
            if "current_rate" in fr:
                current_rate = fr["current_rate"]
                summary_parts.append(f"- Current Funding Rate: {current_rate:.4f}%")
                
        # Add market depth
        if "market_depth" in liq and liq["market_depth"]:
            md = liq["market_depth"]
            if "bid_ask_ratio" in md:
                ratio = md["bid_ask_ratio"]
                bias = "buy" if ratio > 1.0 else "sell"
                summary_parts.append(f"- Bid/Ask Ratio: {ratio:.2f} ({bias} bias)")
        
        # Add futures basis
        if "futures_basis" in liq and liq["futures_basis"]:
            fb = liq["futures_basis"]
            if "annualized_basis" in fb:
                basis = fb["annualized_basis"]
                summary_parts.append(f"- Futures Annualized Basis: {basis:.2f}%")
    
    return "\n".join(summary_parts)