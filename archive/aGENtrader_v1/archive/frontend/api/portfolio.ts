import { Router } from 'express';
import { storage } from '../storage';
import { log } from '../vite';
import { currentPrices } from '../trading';

const router = Router();

// GET portfolio data endpoint
router.get('/', async (req, res) => {
  try {
    // Get trades for the user
    const trades = await storage.getTradesByUserId(req.user?.id || 1);

    // Calculate portfolio based on trades
    const portfolio = trades.reduce((acc, trade) => {
      const amount = trade.type === 'buy' ? trade.quantity : -trade.quantity;

      if (!acc[trade.symbol]) {
        acc[trade.symbol] = 0;
      }
      acc[trade.symbol] += amount;
      return acc;
    }, {} as Record<string, number>);

    // Calculate current values using latest prices
    let total_value_usd = 0;
    const cash_balance = 3211.45; // Demo cash balance
    const assets = Object.entries(portfolio)
      .filter(([_, amount]) => amount > 0) // Only show positive holdings
      .map(([symbol, amount]) => {
        const price = currentPrices[symbol] || 0;
        const value_usd = amount * price;
        total_value_usd += value_usd;

        return {
          asset: symbol,
          amount,
          price,
          value_usd
        };
      });

    total_value_usd += cash_balance;

    log('Portfolio data requested', 'api');
    res.json({
      total_value_usd,
      cash_balance,
      assets,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error fetching portfolio data:', error);
    return res.status(500).json({ error: 'Failed to fetch portfolio data' });
  }
});

export default router;