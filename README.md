# 🔒 Data Anonymizer

A comprehensive web application for anonymizing sensitive data in CSV and Excel files with 14+ anonymization methods, built with FastAPI and Streamlit.

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation & Running

#### One-Command Launch 🚀

**For Windows:**
```powershell
# PowerShell
.\launch.ps1

# Or Command Prompt
launch.bat
```

**For Linux/macOS:**
```bash
./launch.sh
```

This single command will:
- ✅ Set up virtual environment
- ✅ Install all dependencies
- ✅ Generate sample data
- ✅ Start both FastAPI backend and Streamlit frontend
- ✅ Open the web interface automatically

#### Manual Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/hanialnaber/data-anonymizer.git
   cd data-anonymizer
   ```

2. **Create a virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Start the application**:
   ```bash
   # Backend (in one terminal)
   uvicorn src.data_anonymizer.api.main:app --reload --port 8000
   
   # Frontend (in another terminal)
   streamlit run frontend/streamlit_app.py --server.port 8501
   ```

### Stopping the Application

**Quick Stop:**
```bash
# Linux/macOS
./stop.sh

# Windows PowerShell
.\stop.ps1

# Windows Command Prompt
stop.bat
```

**Or press Ctrl+C** in the terminal running the application.

### Accessing the Application

- **Frontend (Streamlit)**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## ✨ Features

### 🎯 Advanced Anonymization Methods
- **14 Anonymization Techniques**: From basic hashing to advanced differential privacy
- **Context-Aware Processing**: Smart detection and handling of different data types
- **Quality Assessment**: Built-in privacy scoring and validation

### 🔐 Privacy Compliance
- **GDPR Ready**: Full compliance with EU privacy regulations
- **HIPAA Support**: Healthcare data anonymization standards
- **PCI DSS**: Payment card data protection

### 🌐 Web Interface
- **Intuitive Frontend**: User-friendly Streamlit interface
- **REST API**: Complete FastAPI backend for integration
- **Real-time Processing**: Live preview and validation
- **Multi-format Support**: CSV, Excel, and multi-sheet files

## 📋 Available Anonymization Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| **Hash** | SHA-256/512 cryptographic hashing | Irreversible anonymization |
| **Pseudonymize** | Consistent fake identifier generation | Maintaining relationships |
| **Remove** | Complete data removal | GDPR right to erasure |
| **Mask** | Partial data masking | Showing data patterns |
| **Substitute** | Random value replacement | General anonymization |
| **Generalize** | Range-based generalization | Age groups, salary bands |
| **Perturb** | Statistical noise addition | Numeric data privacy |
| **K-Anonymity** | Group-based anonymization | Research data |
| **Differential Privacy** | Statistical privacy protection | Advanced privacy |
| **Email Anonymization** | Preserve domain structure | Email analytics |
| **Phone Anonymization** | Format-preserving phone masking | Contact data |
| **SSN Anonymization** | Social Security Number masking | Identity protection |
| **Date Generalization** | Time-based generalization | Temporal privacy |
| **Categorical Generalization** | Category-based grouping | Classification data |

## 🛠️ Project Structure

```
data_anonymizer/
├── src/
│   └── data_anonymizer/
│       ├── core/           # Core anonymization logic
│       │   ├── anonymizer.py
│       │   ├── config.py
│       │   └── security.py
│       ├── api/            # FastAPI backend
│       │   ├── main.py
│       │   └── routes/
│       └── utils/          # Utility functions
├── frontend/               # Streamlit frontend
│   └── streamlit_app.py
├── tests/                  # Comprehensive test suite
├── samples/                # Sample data files
├── config/                 # Configuration files
├── scripts/                # Development scripts
└── docs/                   # Documentation
```

## � Usage Examples

### Basic Usage (Web Interface)

1. **Launch the application** using the launch script
2. **Open** http://localhost:8501 in your browser
3. **Upload** a CSV or Excel file
4. **Select** anonymization methods for each column
5. **Preview** the anonymized data
6. **Download** the anonymized file

### API Usage

```python
import requests
import json

# Upload file
files = {'file': open('data.csv', 'rb')}
response = requests.post('http://localhost:8000/api/v1/upload', files=files)

# Configure anonymization
config = {
    'Sheet1': {
        'name': 'hash',
        'email': 'anonymize_email',
        'phone': 'anonymize_phone',
        'age': {'method': 'generalize_numeric', 'options': {'bin_size': 10}}
    }
}

# Process file
response = requests.post('http://localhost:8000/api/v1/anonymize', data={
    'filename': 'data.csv',
    'output_format': 'csv',
    'masking_config': json.dumps(config)
})
```

### Command Line Usage

```python
from data_anonymizer.core.anonymizer import DataAnonymizer

# Initialize anonymizer
anonymizer = DataAnonymizer()

# Anonymize data
result = anonymizer.anonymize_dataframe(
    data=df,
    config={
        'name': 'hash',
        'email': 'anonymize_email',
        'age': {'method': 'generalize_numeric', 'options': {'bin_size': 10}}
    }
)
```

## 🧪 Testing

The application includes a comprehensive test suite with 111 tests covering all anonymization methods:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_anonymizer.py -v      # Core functionality
python -m pytest tests/test_api.py -v             # API endpoints
python -m pytest tests/test_security.py -v        # Security validation
python -m pytest tests/test_performance.py -v     # Performance benchmarks
python -m pytest tests/test_integration.py -v     # Integration workflows
```

### Test Coverage
- **Core Anonymization**: 30+ tests for all 14 anonymization methods
- **API Endpoints**: 20+ tests for FastAPI routes and error handling
- **Security & Privacy**: 25+ tests for cryptographic security and privacy preservation
- **Performance**: 20+ tests for scalability and memory efficiency
- **Integration**: 15+ tests for end-to-end workflows

## 📊 Sample Data

The application includes sample data for testing:

- `samples/sample_data.csv` - Basic CSV with various data types
- `samples/sample_multisheet.xlsx` - Excel file with multiple sheets

Access these files through the web interface or use them for API testing.

## 🔧 Configuration

### Environment Variables

The application uses the following configuration options:

```python
# In src/data_anonymizer/core/config.py
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = ['.csv', '.xlsx', '.xls']
DEFAULT_HASH_ALGORITHM = "sha256"
```

### Custom Configuration

You can modify anonymization behavior by:

1. **Adjusting method parameters**: Each method supports various options
2. **Creating custom substitution lists**: Add your own replacement values
3. **Modifying privacy levels**: Adjust noise parameters for differential privacy

## 📈 Performance

- **Scalability**: Efficiently handles files up to 100MB
- **Memory Optimization**: Chunked processing for large datasets
- **Parallel Processing**: Multi-threaded anonymization support
- **Caching**: Intelligent caching for repeated operations

## 🔐 Security Features

- **Cryptographically Secure**: Uses secure random number generation
- **Salt-based Hashing**: Prevents rainbow table attacks
- **Format Preservation**: Maintains data utility while ensuring privacy
- **Compliance Ready**: Supports GDPR, HIPAA, and PCI DSS requirements

## 🛡️ Privacy Guarantees

- **Irreversible Anonymization**: Hash-based methods cannot be reversed
- **Deterministic Results**: Same inputs always produce same outputs
- **Privacy-Preserving**: Differential privacy and k-anonymity support
- **Audit Trail**: Track what anonymization methods were applied

## 📖 Documentation

- **API Documentation**: http://localhost:8000/docs (when running)
- **Method Reference**: Detailed documentation for each anonymization method
- **Configuration Guide**: Complete configuration options
- **Security Best Practices**: Guidelines for secure anonymization

## 🎯 Real-World Use Cases

### Healthcare Data
- Patient record anonymization
- Medical research data preparation
- HIPAA compliance

### Financial Services
- Customer data anonymization
- Transaction data processing
- PCI DSS compliance

### Human Resources
- Employee data anonymization
- Performance data sharing
- GDPR compliance

### Research & Analytics
- Dataset sharing
- Privacy-preserving analytics
- Statistical analysis

---

**Note**: This tool is designed for legitimate data anonymization purposes. Always ensure compliance with applicable privacy laws and regulations in your jurisdiction.
