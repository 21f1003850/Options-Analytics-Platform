# Options Analytics Platform

An advanced, production-ready options analytics platform with universal broker integration for backtesting, analyzing, and trading options strategies.

## ✨ Features

### 🔌 Universal Broker Adapter
- Abstract broker interface for seamless integration
- Mock broker with realistic simulated data
- Ready-to-use stubs for IBKR, Zerodha, and Alpaca
- Easy to extend for additional brokers

### 📊 Volatility Analytics
- **3D Volatility Surface** - Visualize IV across strikes and expirations
- **Volatility Skew** - Analyze skew by strike or delta
- **Volatility Smile** - Detect smile patterns per expiration
- **IV Term Structure** - Track IV across time
- **Historical Volatility** - Compare IV vs HV with percentiles

### 📈 Open Interest Analysis
- **Put-Call Ratio (PCR)** - Volume and OI-based sentiment
- **Max Pain** - Calculate pain points for option writers
- **OI Buildup/Unwinding** - Detect position changes
- **Gamma Walls** - Identify high gamma concentration
- **Heatmaps & Charts** - Visualize OI distribution

### 🎯 Strategy Builder
- Visual multi-leg strategy construction
- 15+ pre-built strategy templates
- Real-time payoff diagrams
- Break-even analysis
- Portfolio Greeks aggregation
- Risk metrics (VaR, margin estimation)

### ⏪ Backtesting Engine
- Event-driven backtesting framework
- Performance metrics (Sharpe, Sortino, Calmar, Max DD)
- Monte Carlo simulation
- What-if analysis
- Comprehensive reporting

### 🚀 Modern API
- FastAPI with automatic OpenAPI documentation
- RESTful endpoints for all features
- WebSocket support for real-time data
- Type-safe Pydantic models

## 🏗️ Architecture

```
├── backend/              # Python FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── brokers/     # Broker adapters
│   │   ├── analytics/   # Greeks, volatility, OI analytics
│   │   ├── strategies/  # Strategy builder & templates
│   │   ├── backtesting/ # Backtesting engine
│   │   ├── models/      # Pydantic models
│   │   └── main.py      # FastAPI application
│   └── requirements.txt
├── frontend/            # React + TypeScript frontend (TBD)
├── docs/               # Documentation
├── docker-compose.yml  # Docker orchestration
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/21f1003850/Options-Analytics-Platform.git
cd Options-Analytics-Platform

# Start all services
docker-compose up -d

# Access the API
open http://localhost:8000/docs
```

### Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload

# API will be available at http://localhost:8000
# API documentation at http://localhost:8000/docs
```

## 📖 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key API Endpoints

#### Options & Greeks
- `GET /api/v1/options/chain` - Get option chain with Greeks
- `POST /api/v1/options/greeks/calculate` - Calculate Greeks
- `POST /api/v1/options/iv/calculate` - Calculate implied volatility

#### Volatility Analytics
- `GET /api/v1/volatility/surface` - 3D volatility surface
- `GET /api/v1/volatility/skew` - Volatility skew
- `GET /api/v1/volatility/smile` - Volatility smile
- `GET /api/v1/volatility/term-structure` - IV term structure

#### Open Interest
- `GET /api/v1/oi/pcr` - Put-Call Ratio
- `GET /api/v1/oi/max-pain` - Max Pain calculation
- `GET /api/v1/oi/heatmap` - OI heatmap data
- `GET /api/v1/oi/gamma-walls` - Gamma wall analysis

#### Strategies
- `POST /api/v1/strategies/build` - Build custom strategy
- `POST /api/v1/strategies/payoff` - Calculate payoff diagram
- `POST /api/v1/strategies/analyze` - Comprehensive analysis
- `GET /api/v1/strategies/templates` - Pre-built templates

#### Backtesting
- `POST /api/v1/backtest/run` - Run backtest
- `POST /api/v1/backtest/monte-carlo` - Monte Carlo simulation

## 🧪 Testing

```bash
cd backend

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_greeks.py
```

## 🔧 Configuration

Environment variables can be set in `.env` file:

```env
# Application
APP_NAME=Options Analytics Platform
DEBUG=False

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=options_user
POSTGRES_PASSWORD=options_password
POSTGRES_DB=options_db

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Broker
DEFAULT_BROKER=mock

# Market Data
RISK_FREE_RATE=0.05
```

## 📚 Documentation

- [Architecture Overview](docs/architecture.md)
- [Broker Integration Guide](docs/broker-integration-guide.md)
- [API Reference](http://localhost:8000/docs) (when running)

## 🛠️ Technology Stack

### Backend
- **Python 3.11+**
- **FastAPI** - Modern web framework
- **NumPy & SciPy** - Scientific computing
- **Pandas** - Data manipulation
- **Pydantic** - Data validation

### Database & Caching
- **PostgreSQL** - Persistent storage
- **Redis** - Caching & real-time data

### DevOps
- **Docker** - Containerization
- **docker-compose** - Service orchestration

## 📈 Strategy Templates

The platform includes 15+ pre-built strategy templates:

### Directional Strategies
- Long/Short Call/Put
- Bull/Bear Call Spread
- Bull/Bear Put Spread

### Volatility Strategies
- Long/Short Straddle
- Long/Short Strangle
- Butterfly Spread

### Advanced Strategies
- Iron Condor
- Iron Butterfly
- Calendar Spread
- Diagonal Spread
- Ratio Spread
- Collar

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Black-Scholes option pricing model
- FastAPI framework
- The open-source community

## 📧 Contact

For questions and support, please open an issue on GitHub.

---

**Status**: ✅ Backend Complete | 🚧 Frontend In Progress

Made with ❤️ for options traders