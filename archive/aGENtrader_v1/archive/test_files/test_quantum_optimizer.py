
import asyncio
from agents.quantum_optimizer import QuantumOptimizerAgent

async def test_quantum_optimizer():
    """Test the Quantum Optimizer Agent"""
    print("=== Testing Quantum Optimizer Agent ===")
    
    # Initialize the agent
    optimizer = QuantumOptimizerAgent()
    
    # Run portfolio optimization
    result = await optimizer.optimize_portfolio()
    
    # Display the results
    print("\nPortfolio Optimization Results:")
    print(f"Expected Return: {result['expected_return']}%")
    print(f"Risk Level: {result['risk_level']}")
    print("\nRecommended Portfolio Allocation:")
    for asset, allocation in result['portfolio_allocation'].items():
        print(f"  {asset}: {allocation}%")
    
    print("\nTimestamp:", result['timestamp'])
    print("\nOptimization complete! Results saved to data/portfolio_optimization.json")

if __name__ == "__main__":
    asyncio.run(test_quantum_optimizer())
