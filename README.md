# Consensus AI: Multi-Agent Investment Committee

A multi-agent trading system where three AI agents (Bull, Bear, Risk Manager) debate before executing trades on WEEX.

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configure your API keys
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        CONSENSUS AI                               │
├──────────────────────────────────────────────────────────────────┤
│   WEEX Data  →  Signal Generation  →  Multi-Agent Debate         │
│                                              │                    │
│                                              ▼                    │
│   🐂 Bull ◄────────────► 🐻 Bear ◄────────► ⚖️ Risk Manager      │
│                                              │                    │
│                                              ▼                    │
│                                     Order Execution               │
└──────────────────────────────────────────────────────────────────┘
```

## Key Features

- **Adversarial Validation**: No trade executes without surviving a debate
- **Explainable AI**: Every decision is logged with reasoning
- **Risk-First**: Hard-coded 20x leverage limit enforced by Risk Manager
- **Real-time UI**: Watch the agents argue before your eyes

## License

MIT
