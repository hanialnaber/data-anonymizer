# 🔒 Data Anonymizer

A comprehensive web application for anonymizing sensitive data in CSV and Excel files with 14+ anonymization methods, built with FastAPI and Streamlit.

## 🚀 Quick Start

### For First-Time Users (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/hanialnaber/data-anonymizer.git
   cd data-anonymizer
   ```

2. **Run the launch script**:
   
   **Windows:**
   ```cmd
   launch.bat
   ```
   
   **Linux/macOS:**
   ```bash
   ./launch.sh
   ```
   
   This will automatically:
   - Set up the environment
   - Install dependencies
   - Start the application
   - Open your browser to http://localhost:8501

3. **To stop the application**:
   
   **Windows:**
   ```cmd
   stop.bat
   ```
   
   **Linux/macOS:**
   ```bash
   ./stop.sh
   ```

### Manual Installation (Advanced Users)

If you prefer to install manually:

1. **Prerequisites:**
   - Python 3.8 or higher
   - pip (Python package manager)

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   streamlit run frontend/streamlit_app.py
   ```

4. **Access the application**:
   - Open your browser to: http://localhost:8501

### Usage
1. Upload your CSV or Excel file
2. Select anonymization methods for each column
3. Preview the anonymized data
4. Download the anonymized file

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
- **Real-time Processing**: Live preview and validation
- **Multi-format Support**: CSV, Excel, and multi-sheet files
- **Easy Setup**: One-click launch scripts for all platforms

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
│       └── utils/          # Utility functions
├── frontend/               # Streamlit web interface
│   └── streamlit_app.py
├── samples/                # Sample data files
├── launch.bat/.sh          # Launch scripts
└── stop.bat/.sh           # Stop scripts
```

## 📊 Performance & File Handling

The Data Anonymizer efficiently handles files of all sizes with intelligent processing strategies:

### File Size Categories

| File Size | Rows | Processing Time | Memory Usage | Strategy |
|-----------|------|----------------|--------------|----------|
| **Small** | < 50K | < 5 seconds | ~2-5MB | Direct processing |
| **Medium** | 50K-500K | 5-30 seconds | ~10-50MB | Optimized operations |
| **Large** | 500K-5M | 30-300 seconds | ~50-200MB | Chunked processing |
| **Very Large** | > 5M | Variable | Controlled | Concurrent chunks |

### Processing Features

- **🚀 Automatic Optimization**: Detects file size and chooses optimal processing strategy
- **💾 Memory Management**: Intelligent chunking prevents memory overflow
- **⚡ Concurrent Processing**: Multi-threaded processing for large datasets
- **🔄 Progress Tracking**: Real-time progress bars for long operations
- **🛡️ Error Recovery**: Fallback strategies for memory-limited systems

### Supported Formats

- **CSV Files**: Streaming support, efficient chunked processing
- **Excel Files**: Multi-sheet support, sheet-by-sheet processing
- **Large Files**: Automatic chunking for files > 100MB
- **Memory Optimization**: Garbage collection and memory cleanup

## � Usage Examples

### How to Use

1. **Launch the application** using the launch script above
2. **Open** http://localhost:8501 in your browser (should open automatically)
3. **Upload** a CSV or Excel file
4. **Select** anonymization methods for each column
5. **Preview** the anonymized data
6. **Download** the anonymized file
```

## 📊 Sample Data

The application includes sample data for testing:

- `samples/sample_data.csv` - Basic CSV with various data types  
- `samples/sample_multisheet.xlsx` - Excel file with multiple sheets

Access these files through the web interface or use them for testing.

## ️ Privacy & Security

- **Irreversible Anonymization**: Hash-based methods cannot be reversed
- **Deterministic Results**: Same inputs always produce same outputs  
- **Privacy-Preserving**: Differential privacy and k-anonymity support
- **Compliance Ready**: Supports GDPR, HIPAA, and PCI DSS requirements

## 🎯 Use Cases

- **Healthcare**: Patient record anonymization, HIPAA compliance
- **Financial**: Customer data anonymization, PCI DSS compliance  
- **HR**: Employee data anonymization, GDPR compliance
- **Research**: Dataset sharing, privacy-preserving analytics

---

**Note**: This tool is designed for legitimate data anonymization purposes. Always ensure compliance with applicable privacy laws and regulations in your jurisdiction.
