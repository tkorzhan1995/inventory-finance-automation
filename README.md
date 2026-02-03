# Inventory & Finance Automation System

(https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
(https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

> A finance-first automation system to ensure accurate inventory, COGS, and margin reporting in retail environments. This project replaces manual reconciliations and spreadsheet-based controls with auditable, exception-driven automation.

## Objectives

- Build inventory movement reconciliations (WMS vs ERP)
- Automate COGS postings tied to shipment events
- Detect negative stock or margin anomalies
- Create markdown impact analysis
- Flag shrinkage or unexplained variances

## Architecture

```
inventory-finance-automation/
├── src/
│   ├── reconciliation/          # WMS vs ERP reconciliation
│   │   ├── wms_erp_reconciliation.py
│   │   └── inventory_movement.py
│   ├── cogs/                    # Automated COGS postings
│   │   ├── shipment_event_listener.py
│   │   └── cogs_automation.py
│   ├── anomaly_detection/       # Anomaly detection engines
│   │   ├── negative_stock_detector.py
│   │   ├── margin_anomaly_checker.py
│   │   └── shrinkage_detection.py
│   └── analytics/               # Analytics and reporting
│       ├── markdown_impact_analysis.py
│       └── variance_reporting.py
├── config/                      # Configuration files
│   ├── wms_config.yaml
│   └── erp_config.yaml
├── tests/                       # Unit tests
├── docs/                        # Documentation
└── .github/workflows/           # CI/CD automation
```

## Quick Start

### Prerequisites

- Python 3.9+
- Access to WMS and ERP APIs
- pip package manager

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/tkorzhan1995/inventory-finance-automation.git
cd inventory-finance-automation
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure your systems:**
```bash
cp config/wms_config.yaml.example config/wms_config.yaml
cp config/erp_config.yaml.example config/erp_config.yaml
# Edit the config files with your credentials
```

## Features

### 1. Inventory Reconciliation

Automatically reconcile inventory between WMS and ERP systems:

```python
from src.reconciliation.wms_erp_reconciliation import InventoryReconciliation

reconciliation = InventoryReconciliation()
results = reconciliation.run_daily_reconciliation()
```

**Key Capabilities:**
- Daily automated reconciliation
- Variance detection and reporting
- Root cause analysis
- Automated alerts for significant discrepancies

### 2. COGS Automation

Automatically post COGS entries tied to shipment events:

```python
from src.cogs.shipment_event_listener import ShipmentEventListener

listener = ShipmentEventListener()
listener.start_listening()
```

**Key Capabilities:**
- Real-time shipment event processing
- Multiple costing methods (FIFO, LIFO, Average, Standard)
- Automatic journal entry creation
- Audit trail maintenance

### 3. Anomaly Detection

Detect and flag inventory and margin anomalies:

```python
from src.anomaly_detection.negative_stock_detector import NegativeStockDetector
from src.anomaly_detection.margin_anomaly_checker import MarginAnomalyChecker

# Check for negative stock
detector = NegativeStockDetector()
negative_items = detector.scan_and_report()

# Check for margin anomalies
margin_checker = MarginAnomalyChecker()
anomalies = margin_checker.detect_anomalies()
```

**Key Capabilities:**
- Real-time negative stock detection
- Statistical margin anomaly detection
- Shrinkage identification
- Automated alerting system

### 4. Markdown Impact Analysis

Analyze the financial impact of markdowns:

```python
from src.analytics.markdown_impact_analysis import MarkdownAnalyzer

analyzer = MarkdownAnalyzer()
impact = analyzer.analyze_markdown_impact(start_date, end_date)
```

**Key Capabilities:**
- Period-over-period markdown analysis
- Category-level impact assessment
- Executive summary reports
- Trend identification

## Configuration

### WMS Configuration (`config/wms_config.yaml`)

```yaml
wms:
  api_endpoint: "https://your-wms-api.com/v1"
  api_key: "${WMS_API_KEY}"
  timeout: 30
  retry_attempts: 3
```

### ERP Configuration (`config/erp_config.yaml`)

```yaml
erp:
  api_endpoint: "https://your-erp-api.com/v1"
  api_key: "${ERP_API_KEY}"
  timeout: 30
  cogs_method: "FIFO"  # FIFO, LIFO, Average, Standard
```

## Running the System

### Manual Execution

```bash
# Run reconciliation
python -m src.reconciliation.wms_erp_reconciliation

# Run COGS automation
python -m src.cogs.shipment_event_listener

# Run anomaly detection
python -m src.anomaly_detection.negative_stock_detector
python -m src.anomaly_detection.margin_anomaly_checker

# Run markdown analysis
python -m src.analytics.markdown_impact_analysis
```

### Automated Execution

The system includes GitHub Actions workflows for automated daily execution. See `.github/workflows/automated_checks.yml`.

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_reconciliation.py
```

## Monitoring & Alerts

The system supports multiple alert channels:

- **Email:** Configure SMTP settings in config
- **Slack:** Add webhook URL to GitHub Secrets
- **Dashboard:** Reports available in `reports/` directory

## Security

- Store API keys in environment variables or GitHub Secrets
- Never commit credentials to the repository
- Use `.env` files locally (included in `.gitignore`)
- Implement IP whitelisting for production APIs

## Documentation

Detailed documentation available in the `docs/` directory:

- [Reconciliation Guide](docs/reconciliation_guide.md)
- [COGS Automation Guide](docs/cogs_automation_guide.md)
- [Anomaly Detection Guide](docs/anomaly_detection_guide.md)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

- **tkorzhan1995** - *Initial work*

## Acknowledgments

- Built for retail finance teams dealing with complex inventory scenarios
- Designed to handle real-world edge cases and exceptions
- Focus on auditability and finance compliance

## Support

For issues, questions, or contributions, please open an issue on GitHub.
