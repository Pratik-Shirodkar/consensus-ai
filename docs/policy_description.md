# Consensus AI: Policy Description Document

## Trading Policy: Adversarial Validation Framework

### Executive Summary

Consensus AI implements an **Adversarial Validation** trading policy where no trade is executed unless it survives a structured debate between three AI agents with opposing mandates. This framework ensures disciplined, risk-managed trading with complete transparency and human-readable justification for every decision.

---

## Core Policy Principles

### 1. Multi-Agent Consensus Requirement

Every trade proposal must pass through a three-stage validation:

| Stage | Agent | Mandate | Veto Power |
|-------|-------|---------|------------|
| 1. Proposal | 🐂 Bull Agent | Identify opportunities | No |
| 2. Challenge | 🐻 Bear Agent | Scrutinize risks | No |
| 3. Arbitration | ⚖️ Risk Manager | Final approval | **Yes** |

**Policy Rule:** A trade is only executed if the Risk Manager approves after hearing both sides.

---

### 2. Trading Logic

#### Signal Generation
- **Momentum Indicators:** RSI, MACD for trend identification
- **Mean Reversion:** Bollinger Bands for overbought/oversold detection
- **Volume Analysis:** Confirms conviction behind price moves
- **Order Book Depth:** Assesses liquidity and slippage risk

#### Debate Workflow
```
1. Market data refreshed every 5 minutes
2. Bull Agent analyzes for LONG opportunities (confidence 0-100%)
3. Bear Agent evaluates risks and may challenge (confidence 0-100%)
4. Risk Manager arbitrates based on:
   - Bull confidence vs. Bear confidence
   - Portfolio exposure limits
   - Hard-coded safety rules
5. Decision: APPROVE / MODIFY / REJECT
6. If approved: Order executed via WEEX API
```

---

### 3. Hard Rules (Immutable)

These rules are enforced in code and cannot be overridden by AI agents:

| Rule | Limit | Enforcement |
|------|-------|-------------|
| **Maximum Leverage** | 20x | Hardcoded cap in Risk Manager |
| **Position Size** | 10% of portfolio | Automatic reduction if exceeded |
| **Stop-Loss Required** | Mandatory | Trade rejected without SL |
| **Portfolio Exposure** | 80% maximum | New trades blocked at limit |

---

### 4. Trade Execution Rationale

Every executed trade includes:
- **Bull's Thesis:** Why enter this trade
- **Bear's Concerns:** Identified risks
- **Risk Manager's Decision:** Final reasoning with any modifications
- **Parameters:** Entry, stop-loss, take-profit, leverage, size

**Sample Trade Log:**
```
[14:32:15] 🐂 Bull: "BTC showing bullish MACD crossover. RSI at 58 with 
           room to run. Volume 1.8x average confirms momentum. 
           Proposing LONG at 42,150 with 5x leverage."

[14:32:18] 🐻 Bear: "Concern: Order book thin on ask side - only $2M 
           in top 10 levels. RSI approaching overbought. 
           Recommend reduced size."

[14:32:22] ⚖️ Risk Manager: "APPROVED with modification. 
           Reducing leverage from 5x to 3x due to thin order book.
           Position size: 5%. SL: 2%. TP: 4%."

[14:32:23] ✅ EXECUTED: BTC-LONG @ $42,150 | 3x | Size: $500
```

---

### 5. Minimum Activity Guarantee

To satisfy the 10-trade minimum:
- Agents analyze every 5-minute candle
- Lower timeframe increases debate frequency
- Conservative parameters ensure trade viability

Expected activity: **15-30 debates per day**, resulting in **8-15 approved trades**.

---

## Risk Philosophy

> "The goal is not to maximize trades, but to maximize the quality of trades that survive adversarial scrutiny."

By requiring consensus between opposing viewpoints, we:
- Reduce impulse trading
- Document reasoning for every decision
- Catch blind spots through diverse perspectives
- Maintain disciplined risk management

---

## Compliance Summary

| Requirement | How We Meet It |
|-------------|----------------|
| Leverage ≤ 20x | Hard-coded limit, cannot be bypassed |
| Minimum 10 trades | 5-minute debate cycles ensure activity |
| Policy Document | This document + real-time debate logs |
| AI Participation | See companion AI Description document |
| Code Repository | GitHub with full architecture |

---

*Consensus AI - Where AI agents debate so your portfolio doesn't have to gamble.*
