# Architecture Overview

## System Design

The Options Analytics Platform follows a modular, layered architecture designed for scalability, maintainability, and extensibility.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│                  (React + TypeScript + Vite)                │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         API Layer                            │
│                      (FastAPI + Pydantic)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
│  Broker Adapters │ │  Analytics   │ │  Strategies  │
│                  │ │  Engine      │ │  & Backtest  │
└──────────────────┘ └──────────────┘ └──────────────┘
                ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│              (PostgreSQL + Redis + Market Data)             │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Broker Adapter Layer

**Purpose**: Abstract broker-specific implementations to provide a unified interface

**Components**:
- `IBrokerAdapter`: Abstract interface defining required methods
- `BrokerFactory`: Factory pattern for instantiating adapters
- `MockBrokerAdapter`: Simulated broker for testing
- Broker-specific adapters (IBKR, Zerodha, Alpaca)

**Design Patterns**:
- **Adapter Pattern**: Translates broker-specific APIs to common interface
- **Factory Pattern**: Creates appropriate adapter instances
- **Strategy Pattern**: Different brokers, same interface

**Benefits**:
- Easy to add new brokers
- Testable with mock broker
- Consistent API across all brokers

### 2. Analytics Engine

#### 2.1 Greeks Calculation
- Black-Scholes implementation
- Implied volatility calculation (Newton-Raphson + Bisection)
- All Greeks: Delta, Gamma, Theta, Vega, Rho

#### 2.2 Volatility Analytics
- **Surface**: 3D IV surface across strikes and expirations
- **Skew**: IV by strike or delta
- **Smile**: Per-expiration smile patterns
- **Term Structure**: IV across time
- **Historical**: HV calculation, IV vs HV comparison

#### 2.3 Open Interest Analytics
- **PCR**: Put-Call Ratio (sentiment indicator)
- **Max Pain**: Pain calculation for option writers
- **OI Analysis**: Buildup/unwinding detection
- **Charts**: Heatmaps, distributions, waterfalls

### 3. Strategy Builder

**Purpose**: Construct and analyze multi-leg options strategies

**Components**:
- `StrategyBuilder`: Core builder class
- `StrategyLeg`: Individual position representation
- Strategy templates (15+ pre-built strategies)

**Features**:
- Multi-leg construction
- Validation
- Payoff diagram calculation
- Break-even analysis
- Portfolio Greeks aggregation
- Risk metrics (VaR, margin)

### 4. Backtesting Engine

**Architecture**: Event-driven

**Components**:
- `BacktestEngine`: Main orchestrator
- `Portfolio`: Position and P&L tracking
- `DataHandler`: Historical data management
- `PerformanceMetrics`: Sharpe, Sortino, Max DD
- `MonteCarloSimulator`: Probabilistic analysis

**Flow**:
1. Load historical data
2. Generate signals from strategy
3. Execute orders with commissions/slippage
4. Track portfolio equity
5. Calculate performance metrics

### 5. API Layer

**Framework**: FastAPI

**Features**:
- Automatic OpenAPI documentation
- Type validation with Pydantic
- Async/await support
- WebSocket for real-time data

**Endpoints**:
- `/api/v1/options/*` - Option chains and Greeks
- `/api/v1/volatility/*` - Volatility analytics
- `/api/v1/oi/*` - Open interest analytics
- `/api/v1/strategies/*` - Strategy builder
- `/api/v1/backtest/*` - Backtesting

### 6. Data Layer

**Databases**:
- **PostgreSQL**: Persistent storage for historical data, strategies, backtest results
- **Redis**: Caching, real-time quotes, session management

**Schema** (Planned):
- `option_chains`: Historical option chain snapshots
- `strategies`: User-saved strategies
- `backtests`: Backtest configurations and results
- `users`: User accounts (future)

## Data Flow

### Option Chain Retrieval

```
Client Request
    │
    ▼
API Endpoint (/api/v1/options/chain)
    │
    ▼
BrokerFactory.create(broker_name)
    │
    ▼
MockBrokerAdapter.get_option_chain()
    │
    ▼
Generate realistic option data
    │
    ▼
Calculate Greeks (Black-Scholes)
    │
    ▼
Return OptionContract[]
    │
    ▼
API Response (JSON)
```

### Volatility Surface Generation

```
Option Chain Data
    │
    ▼
Group by expiration
    │
    ▼
Create strike grid
    │
    ▼
Interpolate missing IV values (scipy.griddata)
    │
    ▼
Calculate moneyness
    │
    ▼
Return surface data (strikes, expiries, IV matrix)
```

### Strategy Backtesting

```
Strategy Definition + Historical Data
    │
    ▼
BacktestEngine.run()
    │
    ├─► Load data for each date
    │   │
    │   ▼
    ├─► Generate signals from strategy function
    │   │
    │   ▼
    ├─► Execute orders (with commission/slippage)
    │   │
    │   ▼
    ├─► Update portfolio equity
    │   │
    │   ▼
    └─► Repeat for all dates
    │
    ▼
Calculate performance metrics
    │
    ▼
Return BacktestResult
```

## Scalability Considerations

### Current Design (MVP)
- Single-instance deployment
- In-memory caching with Redis
- Synchronous broker calls
- Client-side chart rendering

### Future Enhancements

1. **Horizontal Scaling**
   - Load balancer for API instances
   - Shared Redis cluster
   - Database read replicas

2. **Async Processing**
   - Celery/RQ for background tasks
   - Queue for backtests and heavy analytics
   - WebSocket notifications on completion

3. **Caching Strategy**
   - Redis for hot data (quotes, recent chains)
   - PostgreSQL for historical data
   - CDN for static assets

4. **Real-Time Data**
   - WebSocket pools for broker connections
   - Pub/sub pattern for quote distribution
   - Server-side event streaming

## Security

### Current Measures
- CORS configuration
- Environment variable secrets
- Input validation with Pydantic

### Planned
- JWT authentication
- API rate limiting
- Encryption at rest
- Audit logging

## Technology Choices

### Why FastAPI?
- Async/await support for concurrent requests
- Automatic API documentation
- Type safety with Pydantic
- High performance (Starlette + Uvicorn)

### Why PostgreSQL?
- ACID compliance for financial data
- JSON support for flexible schemas
- Excellent query performance
- Mature ecosystem

### Why Redis?
- Sub-millisecond latency for quotes
- Pub/sub for real-time updates
- Simple key-value caching
- Horizontal scalability

## Development Workflow

```
1. Feature Branch
   │
   ▼
2. Implementation
   │
   ▼
3. Unit Tests
   │
   ▼
4. Integration Tests
   │
   ▼
5. Code Review
   │
   ▼
6. Merge to Main
   │
   ▼
7. CI/CD Pipeline
   │
   ▼
8. Deployment
```

## Monitoring & Observability (Planned)

- **Logging**: Structured logs with correlation IDs
- **Metrics**: Prometheus + Grafana
- **Tracing**: OpenTelemetry
- **Alerting**: PagerDuty/Slack integration

## Testing Strategy

### Unit Tests
- Pure functions (Greeks, analytics)
- Strategy builder logic
- Data transformations

### Integration Tests
- API endpoint tests
- Broker adapter tests
- Database operations

### End-to-End Tests
- Full user workflows
- WebSocket connections
- Backtest execution

## Deployment

### Docker Compose (Development)
```yaml
services:
  - postgres (database)
  - redis (cache)
  - backend (API)
  - frontend (UI)
```

### Production (Planned)
- Kubernetes cluster
- Helm charts
- Auto-scaling
- Blue-green deployments

## Performance Targets

- API Response Time: <200ms (p95)
- Option Chain Retrieval: <500ms
- Volatility Surface: <1s
- Backtest (1 year daily): <5s
- WebSocket Latency: <50ms

## Future Roadmap

1. **Phase 2**: Complete frontend with React
2. **Phase 3**: User authentication and multi-tenancy
3. **Phase 4**: Real broker integrations
4. **Phase 5**: Paper trading
5. **Phase 6**: Live trading (with extensive testing)
6. **Phase 7**: Mobile app

---

This architecture is designed to be modular, testable, and scalable while remaining simple enough for rapid development and iteration.
