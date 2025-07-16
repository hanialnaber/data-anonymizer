# 🔒 Data Anonymizer

A comprehensive web application for anonymizing sensitive data in CSV and Excel files with 14+ anonymization methods, built with FastAPI and Streamlit.

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/data-anonymizer.git
   cd data-anonymizer
   ```

2. **Create a virtual environment** (recommended):
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
   ```

4. **Install the package in development mode**:
   ```bash
   pip install -e .
   ```

### Running the Application

#### Option 1: One-Command Launch (Recommended) 🚀

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

#### Option 2: Advanced Launch Options

**Setup only (no start):**
```bash
# Linux/macOS
./launch.sh --setup-only

# Windows PowerShell
.\launch.ps1 -SetupOnly
```

**Skip dependency installation:**
```bash
# Linux/macOS
./launch.sh --no-deps

# Windows PowerShell
.\launch.ps1 -NoDeps
```

**Skip sample data generation:**
```bash
# Linux/macOS
./launch.sh --no-samples

# Windows PowerShell
.\launch.ps1 -NoSamples
```

#### Option 3: Manual Setup (Alternative)
```bash
# Run both backend and frontend together
python scripts/dev.py dev
```

#### Option 4: Run Services Separately
```bash
# Terminal 1: Start the backend API
python scripts/dev.py backend

# Terminal 2: Start the frontend
python scripts/dev.py frontend
```

#### Option 5: Using Make Commands
```bash
# Run both services
make dev

# Or run individually
make backend    # Backend only
make frontend   # Frontend only
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

**Or press Ctrl+C** in the terminal running the launch script.

### Accessing the Application

- **Frontend (Streamlit)**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### First-Time Setup

1. **Generate sample data** (optional):
   ```bash
   python scripts/dev.py samples
   ```

2. **Try the application**:
   - Open http://localhost:8501 in your browser
   - Upload a CSV or Excel file
   - Select anonymization methods for each column
   - Download the anonymized file

## ✨ Features

### 🎯 Advanced Anonymization Methods
- **14 Anonymization Techniques**: From basic hashing to advanced differential privacy
- **Context-Aware Processing**: Smart detection and handling of different data types (emails, phones, SSNs)
- **Configurable Security**: Multiple hash algorithms (SHA-256, SHA-512) and privacy levels
- **Quality Assessment**: Built-in privacy scoring and validation

### 🔐 Enterprise Security
- **File Validation**: Comprehensive security checks for uploaded files
- **Cryptographic Security**: Secure random generation and salt-based hashing
- **Audit Logging**: Complete operation tracking and compliance reporting
- **Auto-Cleanup**: Automatic temporary file management

### 📊 Privacy Compliance
- **GDPR Ready**: Full compliance with EU privacy regulations
- **HIPAA Support**: Healthcare data anonymization standards
- **Audit Trail**: Complete operation logging for compliance

### 🌐 Web Interface
- **Intuitive Frontend**: User-friendly Streamlit interface
- **REST API**: Complete FastAPI backend for integration
- **Real-time Processing**: Live preview and validation
- **Multi-format Support**: CSV, Excel, and multi-sheet files

## 📋 Available Anonymization Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| **Hash** | SHA-256/512 cryptographic hashing | Irreversible anonymization |
| **Pseudonymize** | Consistent fake name generation | Maintaining relationships |
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

## 🛠️ Development

### Project Structure
```
data_anonymizer/
├── src/
│   └── data_anonymizer/
│       ├── core/           # Core anonymization logic
│       ├── api/            # FastAPI backend
│       └── utils/          # Utility functions
├── frontend/               # Streamlit frontend
├── scripts/                # Development scripts
├── samples/                # Sample data files
├── config/                 # Configuration files
└── docs/                   # Documentation
```

### Running Development Commands

```bash
# Format code
make format

# Run linting
make lint

# Type checking
make type-check

# Security checks
make security-check

# All quality checks
make pre-commit
```

### Docker Support

```bash
# Build Docker image
make docker-build

# Run with Docker Compose
make docker-run

# Stop Docker containers
make docker-stop
```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Security settings
SECRET_KEY=your-secret-key-here
HASH_ALGORITHM=sha256
ENABLE_AUDIT_LOG=true

# File upload settings
MAX_FILE_SIZE=10MB
ALLOWED_EXTENSIONS=.csv,.xlsx,.xls

# Performance settings
CHUNK_SIZE=1000
WORKER_THREADS=4
```

### Custom Configuration

You can modify settings in `config/settings.py`:

```python
# Anonymization settings
DEFAULT_HASH_ALGORITHM = "sha256"
DEFAULT_PRIVACY_LEVEL = "medium"
ENABLE_DIFFERENTIAL_PRIVACY = True

# Security settings
ENABLE_FILE_VALIDATION = True
ENABLE_AUDIT_LOGGING = True
AUTO_CLEANUP_ENABLED = True
```

## 📊 Usage Examples

### Basic Usage (Web Interface)

1. **Upload File**: Drag and drop or select CSV/Excel file
2. **Configure Methods**: Choose anonymization method for each column
3. **Preview**: Review anonymized data sample
4. **Download**: Get anonymized file

### API Usage

```python
import requests

# Upload file
files = {'file': open('data.csv', 'rb')}
response = requests.post('http://localhost:8000/upload', files=files)
file_id = response.json()['file_id']

# Configure anonymization
config = {
    'Sheet1': {
        'name': 'hash',
        'email': 'anonymize_email',
        'phone': 'anonymize_phone',
        'age': 'generalize_numeric'
    }
}

# Process file
response = requests.post('http://localhost:8000/anonymize', json={
    'file_id': file_id,
    'config': config,
    'output_format': 'csv'
})

# Download result
with open('anonymized_data.csv', 'wb') as f:
    f.write(response.content)
```

### Command Line Usage

```python
from data_anonymizer.core.anonymizer import DataAnonymizer

# Initialize anonymizer
anonymizer = DataAnonymizer()

# Anonymize data
result = anonymizer.anonymize_dataset(
    data=df,
    config={
        'name': 'hash',
        'email': 'anonymize_email',
        'age': 'generalize_numeric'
    }
)
```

## 🔒 Security Features

### File Validation
- **Type Checking**: Validates file extensions and MIME types
- **Size Limits**: Configurable maximum file size
- **Content Scanning**: Checks for malicious content
- **Path Traversal Protection**: Prevents directory traversal attacks

### Cryptographic Security
- **Secure Hashing**: SHA-256/512 with salt
- **Random Generation**: Cryptographically secure random values
- **Key Management**: Secure key storage and rotation
- **Privacy Levels**: Configurable anonymization strength

### Audit and Compliance
- **Operation Logging**: Complete audit trail
- **Privacy Scoring**: Quantitative privacy assessment
- **Compliance Reporting**: GDPR/HIPAA compliance reports
- **Data Lineage**: Track data transformation history

## 🔍 Sample Data

The application includes comprehensive sample data for testing:

### Available Samples
- **Basic CSV**: Simple employee data with names, emails, ages
- **Healthcare Data**: HIPAA-compliant medical records
- **Financial Data**: Banking information with account numbers
- **Multi-sheet Excel**: Complex datasets with multiple sheets
- **Performance Data**: Large datasets for performance testing

### Generate Samples
```bash
# Generate all sample files
python scripts/dev.py samples

# Files created in samples/ directory:
# - employee_data.csv
# - healthcare_sample.xlsx
# - financial_records.csv
# - performance_test.csv
```

## 📈 Performance

- **Scalability**: Handles files up to 100MB efficiently
- **Memory Optimization**: Chunked processing for large datasets
- **Parallel Processing**: Multi-threaded anonymization
- **Caching**: Intelligent caching for repeated operations

##  Documentation

### API Documentation
- **Interactive Docs**: http://localhost:8000/docs
- **OpenAPI Spec**: http://localhost:8000/openapi.json
- **Redoc**: http://localhost:8000/redoc
