#!/usr/bin/env python3
"""
Test script for AI Log Upload to WEEX
Run this to verify your AI log upload is working correctly.
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from data.ai_log_uploader import ai_log_uploader


async def test_strategy_generation_log():
    """Test uploading a Strategy Generation AI log"""
    print("\n" + "="*60)
    print("Testing: Strategy Generation AI Log Upload")
    print("="*60)
    
    result = await ai_log_uploader.upload_ai_log(
        stage="Strategy Generation",
        model="Claude-3.5-sonnet (AWS Bedrock)",
        input_data={
            "prompt": "Analyze BTC/USDT price trend for the next 3 hours.",
            "data": {
                "RSI_14": 42.5,
                "EMA_20": 94250.0,
                "MACD": 125.3,
                "BB_Upper": 95000.0,
                "BB_Lower": 93500.0,
                "FundingRate": -0.0015,
                "OpenInterest": 485.2
            }
        },
        output_data={
            "signal": "Buy",
            "confidence": 0.75,
            "target_price": 95500,
            "stop_loss": 93000,
            "reason": "RSI oversold recovery, price bouncing off lower BB with negative funding suggesting short squeeze potential."
        },
        explanation="Consensus AI strategy generation analyzed multiple technical indicators. RSI at 42.5 suggests neutral-to-oversold conditions with room for upside. Price near EMA20 support with negative funding rate indicates short-side pressure. MACD positive momentum. Generated bullish signal with 75% confidence targeting $95,500."
    )
    
    print(f"\nResponse: {result}")
    return result.get("code") == "00000"


async def test_decision_making_log():
    """Test uploading a Decision Making AI log"""
    print("\n" + "="*60)
    print("Testing: Decision Making AI Log Upload")
    print("="*60)
    
    result = await ai_log_uploader.upload_ai_log(
        stage="Decision Making",
        model="Claude-3.5-sonnet (AWS Bedrock)",
        input_data={
            "prompt": "Multi-agent debate for BTC/USDT trading decision",
            "bull_analysis": {
                "action": "LONG",
                "confidence": 0.78,
                "reasoning": "Strong support at $94,000 with bullish divergence on RSI"
            },
            "bear_analysis": {
                "action": "SHORT", 
                "confidence": 0.45,
                "reasoning": "Resistance at $96,000 may cap gains"
            },
            "market_data": {
                "symbol": "cmt_btcusdt",
                "price": 94500,
                "24h_change": 2.3
            }
        },
        output_data={
            "decision": "APPROVE",
            "action": "LONG",
            "position_size_pct": 3.0,
            "stop_loss_pct": 2.0,
            "take_profit_pct": 4.0,
            "net_confidence": 0.65,
            "reasoning": "Bull case stronger with 78% vs 45% confidence. Risk-adjusted position approved."
        },
        explanation="Consensus AI multi-agent debate system evaluated Bull vs Bear perspectives. Bull agent presented stronger technical case with 78% confidence citing support levels and RSI divergence. Bear's concerns noted but weaker at 45% confidence. Risk Manager approved modified position with conservative 3% sizing and tight risk controls."
    )
    
    print(f"\nResponse: {result}")
    return result.get("code") == "00000"


async def test_risk_assessment_log():
    """Test uploading a Risk Assessment AI log"""
    print("\n" + "="*60) 
    print("Testing: Risk Assessment AI Log Upload")
    print("="*60)
    
    result = await ai_log_uploader.log_risk_assessment(
        symbol="cmt_btcusdt",
        proposed_action="LONG",
        risk_factors={
            "volatility": "medium",
            "exposure_pct": 15.0,
            "max_drawdown_risk": 3.5,
            "correlation_risk": "low",
            "liquidity_score": 0.92,
            "risk_level": "moderate"
        },
        approved=True,
        position_size=3.0,
        reasoning="Portfolio exposure within acceptable limits. Volatility moderate. Liquidity sufficient for proposed size. Approved with standard stop-loss parameters."
    )
    
    print(f"\nResponse: {result}")
    return result.get("code") == "00000"


async def main():
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║           AI Wars: WEEX AI Log Upload Test                       ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  This script tests the AI log upload API for hackathon          ║
    ║  compliance verification.                                        ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    results = []
    
    # Test 1: Strategy Generation
    try:
        success = await test_strategy_generation_log()
        results.append(("Strategy Generation", success))
    except Exception as e:
        print(f"❌ Error: {e}")
        results.append(("Strategy Generation", False))
    
    await asyncio.sleep(1)  # Brief delay between requests
    
    # Test 2: Decision Making
    try:
        success = await test_decision_making_log()
        results.append(("Decision Making", success))
    except Exception as e:
        print(f"❌ Error: {e}")
        results.append(("Decision Making", False))
    
    await asyncio.sleep(1)
    
    # Test 3: Risk Assessment
    try:
        success = await test_risk_assessment_log()
        results.append(("Risk Assessment", success))
    except Exception as e:
        print(f"❌ Error: {e}")
        results.append(("Risk Assessment", False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    total_passed = sum(1 for _, s in results if s)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("\n🎉 All AI log uploads successful! You're ready for hackathon compliance.")
    else:
        print("\n⚠️ Some uploads failed. Check your API credentials and UID allowlist status.")


if __name__ == "__main__":
    asyncio.run(main())
