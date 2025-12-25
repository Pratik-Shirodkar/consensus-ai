# Consensus AI: AI/ML Participation Description

## Overview

Consensus AI uses **Large Language Models (LLMs)** combined with **quantitative technical analysis** to create a multi-agent trading system. This document explains how AI/ML is integrated and the technical implementation details.

---

## AI Architecture

### Dual-Layer Intelligence

```
┌─────────────────────────────────────────────────────────────────┐
│                     NUMERICAL LAYER                              │
│   Technical Indicators (RSI, MACD, Bollinger, ATR, Volume)       │
│   Pure mathematics - fast, deterministic signal generation       │
└────────────────────────────┬────────────────────────────────────┘
                             │ Signals feed into
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     REASONING LAYER                              │
│   LLM Agents (GPT-4o-mini) interpret signals contextually       │
│   Generate natural language reasoning and debate                │
└─────────────────────────────────────────────────────────────────┘
```

---

## AI Component Breakdown

### 1. Signal Generation (Classical ML/Statistics)

**Technology:** pandas-ta, NumPy

**Indicators Calculated:**
| Indicator | Purpose | Calculation |
|-----------|---------|-------------|
| RSI (14) | Momentum | Relative Strength Index |
| MACD (12,26,9) | Trend | Moving Average Convergence Divergence |
| Bollinger Bands | Volatility | 20-period SMA ± 2σ |
| ATR (14) | Risk Sizing | Average True Range |
| Volume SMA | Confirmation | 20-period volume average |

**Output:** Structured TechnicalSignal objects with value, strength, and description.

---

### 2. LLM Agents (Generative AI)

**Model:** OpenAI GPT-4o-mini (via API)

**Why This Model:**
- Fast inference (~500ms per response)
- Cost-effective for high-frequency analysis
- Strong reasoning capabilities
- JSON output reliability

**Agent Personas:**

#### 🐂 Bull Agent
- **System Prompt Focus:** Identify momentum, breakouts, long opportunities
- **Input:** Market data + technical signals
- **Output:** Trade proposals with confidence scores (JSON)
- **Personality:** Optimistic but data-driven

#### 🐻 Bear Agent  
- **System Prompt Focus:** Challenge bullish bias, identify risks
- **Input:** Bull's proposal + market data
- **Output:** Challenges, agreements, or counter-proposals (JSON)
- **Personality:** Skeptical, risk-aware

#### ⚖️ Risk Manager
- **System Prompt Focus:** Portfolio protection, rule enforcement
- **Input:** Bull vs Bear debate + portfolio state
- **Output:** APPROVE / MODIFY / REJECT decisions
- **Personality:** Stern, rule-following, may "scold" other agents

---

### 3. Debate Orchestration

**Technology:** Custom Python async orchestration

**Flow:**
```python
async def run_debate_cycle(market_data):
    # Phase 1: Bull analyzes
    bull_analysis = await bull_agent.analyze(market_data, signals)
    
    # Phase 2: Bear responds
    bear_response = await bear_agent.respond_to(bull_analysis, market_data)
    
    # Phase 3: Risk Manager decides
    decision = await risk_manager.arbitrate(
        bull_analysis, 
        bear_response,
        portfolio_exposure
    )
    
    return decision
```

**Key Innovation:** Agents maintain conversation context, enabling coherent multi-turn debates.

---

## AI Decision Framework

### Confidence Scoring

Each agent outputs a confidence score (0.0 - 1.0):

```json
{
  "action": "PROPOSE_LONG",
  "confidence": 0.85,
  "reasoning": "MACD bullish crossover with volume confirmation..."
}
```

### Risk Manager Decision Matrix

| Bull Confidence | Bear Confidence | Typical Decision |
|-----------------|-----------------|------------------|
| > 80% | < 50% | APPROVE |
| > 70% | 50-60% | MODIFY (reduce size) |
| Any | > 70% | REJECT |
| 50-60% | 50-60% | REJECT (wait for clarity) |

---

## Prompt Engineering

### System Prompt Structure

Each agent receives:
1. **Persona definition** - personality and objectives
2. **Signal watchlist** - what indicators to prioritize
3. **Output format** - exact JSON schema required
4. **Rules** - constraints (e.g., max leverage suggestions)
5. **Speaking style** - how to communicate

**Example (Bull Agent excerpt):**
```
You are the BULL AGENT on an AI trading committee. 
Your role is to identify LONG opportunities.

PERSONALITY: Optimistic but data-driven...

OUTPUT FORMAT:
{
  "action": "PROPOSE_LONG",
  "confidence": 0.85,
  "suggested_leverage": 5,
  ...
}
```

---

## Safety Mechanisms

### Hard-Coded Overrides

The AI cannot bypass these rules (enforced in Python, not prompts):

```python
# In risk_manager.py
MAX_LEVERAGE = 20  # Absolute cap
MAX_POSITION_SIZE = 0.10  # 10% of portfolio

if proposed_leverage > MAX_LEVERAGE:
    proposed_leverage = MAX_LEVERAGE
    # Log violation and potentially scold agent
```

### Prompt Injection Protection

- Agent outputs are parsed as structured JSON
- Free-form text is only used for display, not execution
- All trading parameters are validated programmatically

---

## Innovation Highlights

1. **Adversarial AI Design:** Three agents with conflicting objectives reach consensus
2. **Explainable Trading:** Every decision includes human-readable reasoning
3. **Dual Intelligence:** Combines speed of numerical analysis with contextual reasoning of LLMs
4. **Self-Documenting:** Debate logs serve as automatic policy documentation
5. **Personality-Driven Agents:** Each agent has distinct "character" for engaging output

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| LLM Provider | OpenAI API (GPT-4o-mini) |
| Python Framework | FastAPI + asyncio |
| Technical Analysis | pandas-ta, NumPy |
| Communication | WebSocket (real-time streaming) |
| Frontend | React 18 + TradingView Charts |

---

## Sample AI Output

```
[15:42:11] 🐂 Bull Agent (82% confident):
"Strong setup detected. RSI at 55 crossing above 50, MACD histogram 
turned positive 3 candles ago and expanding. Volume 1.6x average 
confirms momentum. Order book shows good depth with $5M bid support.
Proposing LONG on BTC/USDT @ $43,250 with 5x leverage, 2% SL, 4% TP."

[15:42:14] 🐻 Bear Agent (45% confident):
"Acknowledging the momentum signals. However, funding rate at +0.02% 
suggests crowded long positioning. Weekly RSI approaching 65 - 
not overbought yet but worth noting. I don't have a strong objection 
but recommend conservative sizing."

[15:42:17] ⚖️ Risk Manager:
"APPROVED. Bull's momentum case is solid, Bear's concerns are minor.
Current exposure at 25% allows this trade.
Final parameters: 5x leverage, 3% position size, SL 2%, TP 4%.
Execution authorized."
```

---

*Consensus AI - Cutting-edge multi-agent AI for disciplined crypto trading.*
