# Data Anonymizer Architecture Guide

## Overview
This document explains the architecture of the Data Anonymizer system, detailing where processing occurs (backend vs frontend) and how different components interact.

## Architecture Summary

### 🔧 Backend Processing (FastAPI)
- **Location**: `src/data_anonymizer/`
- **Purpose**: Core data processing, anonymization algorithms, file handling
- **Port**: 8000 (default)

### 🖥️ Frontend Processing (Streamlit)
- **Location**: `frontend/`
- **Purpose**: User interface, file upload/download, API communication
- **Port**: 8501 (default)

---

## Processing Distribution

### Backend Responsibilities ✅

#### 1. Core Anonymization Processing
**Location**: `src/data_anonymizer/core/anonymizer.py`

```python
class DataAnonymizer:
    """Data anonymization with multiple techniques."""
    
    def __init__(self, salt: Optional[str] = None):
        """Initialize the anonymizer with optional salt."""
        self.salt = salt or "default_salt"
        self.config = Config()
        self.secure_random = secrets.SystemRandom()
    
    def anonymize_dataframe(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Anonymize a pandas DataFrame based on configuration."""
        # Core processing happens here
        anonymized_df = df.copy()
        
        for column_name, method_config in config.items():
            if column_name in df.columns:
                method = method_config.get("method", "hash")
                
                if method == "hash":
                    anonymized_df[column_name] = df[column_name].apply(
                        lambda x: self._generate_secure_hash(x) if pd.notna(x) else x
                    )
                elif method == "mask":
                    anonymized_df[column_name] = df[column_name].apply(
                        lambda x: self._mask_value(x) if pd.notna(x) else x
                    )
                # Additional methods...
        
        return anonymized_df
```

#### 2. File Processing & Memory Management
**Location**: `src/data_anonymizer/core/anonymizer.py`

```python
def load_data(file_path: str, file_type: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    """Load data with memory optimization based on file size."""
    file_size = os.path.getsize(file_path)
    
    # Large file handling (>100MB)
    if file_size > 100 * 1024 * 1024:
        if file_type == "csv":
            # Chunked processing for large CSV files
            chunks = []
            for chunk in pd.read_csv(file_path, chunksize=10000):
                chunks.append(chunk)
            return pd.concat(chunks, ignore_index=True)
        
        elif file_type in ["xlsx", "xls"]:
            # Sheet-by-sheet processing for large Excel files
            return pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
    
    # Standard loading for smaller files
    if file_type == "csv":
        return pd.read_csv(file_path)
    elif file_type in ["xlsx", "xls"]:
        return pd.read_excel(file_path, sheet_name=sheet_name)
```

#### 3. API Route Processing
**Location**: `src/data_anonymizer/api/routes/anonymizer.py`

```python
@router.post("/anonymize")
async def anonymize_data(
    background_tasks: BackgroundTasks,
    filename: str = Form(...),
    output_format: str = Form(...),
    masking_config: str = Form(...),
    selected_sheet: Optional[str] = Form(None),
):
    """Backend API endpoint for anonymization processing."""
    try:
        # Parse configuration
        config_dict = json.loads(masking_config)
        
        # Locate input file
        uploads_path = Path("uploads") / filename
        samples_path = Path("samples") / filename
        
        if uploads_path.exists():
            input_path = uploads_path
        elif samples_path.exists():
            input_path = samples_path
        else:
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        # Generate output path
        output_filename = f"anonymized_{input_path.name}"
        output_path = Path("uploads") / output_filename
        
        # Add background task for processing
        background_tasks.add_task(
            run_anonymization_job,
            str(input_path),
            str(output_path),
            input_path.suffix.lower().replace(".", ""),
            masking_config,
            selected_sheet,
        )
        
        return JSONResponse(content={
            "status": "processing",
            "message": "Anonymization job started",
            "input_file": filename,
            "result_file": output_filename,
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
```

#### 4. Background Job Processing
**Location**: `src/data_anonymizer/core/anonymizer.py`

```python
def run_anonymization_job(
    input_path: str,
    output_path: str,
    file_type: str,
    masking_config: str,
    selected_sheet: Optional[str] = None,
) -> None:
    """Run anonymization job in background."""
    try:
        # Load data with optimization
        df = load_data(input_path, file_type, selected_sheet)
        
        # Initialize anonymizer
        anonymizer = DataAnonymizer()
        
        # Parse configuration
        config = json.loads(masking_config)
        
        # Process data
        anonymized_df = anonymizer.anonymize_dataframe(df, config)
        
        # Save results with proper format
        if file_type == "csv":
            anonymized_df.to_csv(output_path, index=False)
        elif file_type in ["xlsx", "xls"]:
            anonymized_df.to_excel(output_path, index=False, engine='openpyxl')
        
        print(f"✅ Anonymization completed: {output_path}")
        
    except Exception as e:
        print(f"❌ Anonymization failed: {str(e)}")
```

---

### Frontend Responsibilities ✅

#### 1. User Interface & File Upload
**Location**: `frontend/streamlit_app.py`

```python
def main():
    """Main Streamlit application."""
    st.set_page_config(page_title="Data Anonymizer", layout="wide")
    
    # File upload interface
    uploaded_file = st.file_uploader(
        "Choose a file to anonymize",
        type=['csv', 'xlsx', 'xls'],
        help="Upload CSV or Excel files for anonymization"
    )
    
    if uploaded_file is not None:
        # Display file info (frontend processing)
        st.write(f"📁 File: {uploaded_file.name}")
        st.write(f"📊 Size: {uploaded_file.size:,} bytes")
        
        # Send file to backend for processing
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        upload_resp = requests.post(f"{BACKEND_URL}/api/v1/upload/", files=files)
        
        if upload_resp.status_code == 200:
            st.success("✅ File uploaded successfully!")
        else:
            st.error("❌ Upload failed!")
```

#### 2. API Communication
**Location**: `frontend/streamlit_app.py`

```python
def process_anonymization(filename: str, masking_config: dict, selected_sheet: str = None):
    """Send anonymization request to backend API."""
    
    # Prepare data for backend
    data = {
        "filename": filename,
        "output_format": "same",  # Keep original format
        "masking_config": json.dumps(masking_config),
    }
    
    if selected_sheet:
        data["selected_sheet"] = selected_sheet
    
    # Send request to backend
    try:
        response = requests.post(f"{BACKEND_URL}/api/v1/anonymize/", data=data)
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            st.error(f"❌ Processing failed: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Connection error: {str(e)}")
        return None
```

#### 3. Configuration Management (Frontend Only)
**Location**: `frontend/streamlit_app.py`

```python
def create_masking_config(df: pd.DataFrame) -> dict:
    """Create masking configuration from user input (frontend processing)."""
    config = {}
    
    st.subheader("🔒 Configure Anonymization")
    
    for column in df.columns:
        st.write(f"**{column}**")
        
        # User selects method (frontend logic)
        method = st.selectbox(
            f"Method for {column}",
            ["hash", "mask", "pseudonymize", "substitute", "shuffle", "perturb"],
            key=f"method_{column}"
        )
        
        # Configure method parameters (frontend logic)
        if method == "mask":
            mask_char = st.text_input(f"Mask character for {column}", "*", key=f"mask_{column}")
            config[column] = {"method": method, "mask_char": mask_char}
        elif method == "substitute":
            sub_type = st.selectbox(f"Substitution type for {column}", 
                                  ["names", "companies", "cities", "domains"], 
                                  key=f"sub_{column}")
            config[column] = {"method": method, "substitution_type": sub_type}
        else:
            config[column] = {"method": method}
    
    return config
```

---

## Performance Testing

### Backend Performance Tests
**Location**: `tests/test_performance.py`

```python
import pytest
import pandas as pd
from src.data_anonymizer.core.anonymizer import DataAnonymizer, load_data
import time

class TestPerformance:
    """Performance tests for backend processing."""
    
    def test_large_file_processing(self):
        """Test processing of large files (>100MB)."""
        # Create test data
        large_df = pd.DataFrame({
            'name': ['John Doe'] * 1000000,
            'email': ['john@example.com'] * 1000000,
            'phone': ['555-1234'] * 1000000
        })
        
        # Save as CSV
        test_file = "test_large.csv"
        large_df.to_csv(test_file, index=False)
        
        # Test loading with chunked processing
        start_time = time.time()
        df = load_data(test_file, "csv")
        load_time = time.time() - start_time
        
        assert len(df) == 1000000
        assert load_time < 30  # Should load within 30 seconds
        
        # Test anonymization
        anonymizer = DataAnonymizer()
        config = {
            'name': {'method': 'hash'},
            'email': {'method': 'anonymize_email'},
            'phone': {'method': 'anonymize_phone'}
        }
        
        start_time = time.time()
        result_df = anonymizer.anonymize_dataframe(df, config)
        process_time = time.time() - start_time
        
        assert len(result_df) == len(df)
        assert process_time < 60  # Should process within 60 seconds
    
    def test_concurrent_processing(self):
        """Test concurrent processing of multiple files."""
        import concurrent.futures
        
        def process_file(file_data):
            filename, config = file_data
            anonymizer = DataAnonymizer()
            df = pd.read_csv(filename)
            return anonymizer.anonymize_dataframe(df, config)
        
        # Prepare test files
        test_files = [
            ("samples/sample_data.csv", {'name': {'method': 'hash'}}),
            ("samples/sample_data.csv", {'email': {'method': 'anonymize_email'}}),
        ]
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(process_file, test_files))
        
        concurrent_time = time.time() - start_time
        
        # Sequential processing for comparison
        start_time = time.time()
        sequential_results = [process_file(file_data) for file_data in test_files]
        sequential_time = time.time() - start_time
        
        assert len(results) == len(sequential_results)
        assert concurrent_time < sequential_time  # Should be faster
```

### Frontend Performance Tests
**Location**: `tests/test_frontend_performance.py`

```python
import pytest
import requests
import time
from pathlib import Path

class TestFrontendPerformance:
    """Performance tests for frontend-backend communication."""
    
    def test_file_upload_performance(self):
        """Test file upload speed to backend."""
        backend_url = "http://localhost:8000"
        
        # Test with different file sizes
        test_files = [
            "samples/sample_data.csv",  # Small file
            # Add larger test files as needed
        ]
        
        for file_path in test_files:
            if Path(file_path).exists():
                with open(file_path, 'rb') as f:
                    files = {"file": (Path(file_path).name, f, "text/csv")}
                    
                    start_time = time.time()
                    response = requests.post(f"{backend_url}/api/v1/upload/", files=files)
                    upload_time = time.time() - start_time
                    
                    assert response.status_code == 200
                    assert upload_time < 10  # Should upload within 10 seconds
    
    def test_api_response_time(self):
        """Test API response times."""
        backend_url = "http://localhost:8000"
        
        # Test status endpoint
        start_time = time.time()
        response = requests.get(f"{backend_url}/api/v1/status")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 1  # Should respond within 1 second
        
        # Test anonymization endpoint
        data = {
            "filename": "sample_data.csv",
            "output_format": "csv",
            "masking_config": '{"name": {"method": "hash"}}'
        }
        
        start_time = time.time()
        response = requests.post(f"{backend_url}/api/v1/anonymize/", data=data)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 5  # Should start processing within 5 seconds
```

---

## Data Flow Diagram

```
┌─────────────────┐    HTTP/API     ┌─────────────────┐
│   Frontend      │◄──────────────►│    Backend      │
│   (Streamlit)   │                │   (FastAPI)     │
│   Port: 8501    │                │   Port: 8000    │
└─────────────────┘                └─────────────────┘
         │                                   │
         ▼                                   ▼
┌─────────────────┐                ┌─────────────────┐
│ User Interface  │                │ Core Processing │
│ • File Upload   │                │ • DataAnonymizer│
│ • Config UI     │                │ • File I/O      │
│ • Download      │                │ • Background    │
│ • Progress      │                │   Jobs          │
└─────────────────┘                └─────────────────┘
         │                                   │
         ▼                                   ▼
┌─────────────────┐                ┌─────────────────┐
│ API Calls       │                │ Data Storage    │
│ • POST /upload  │                │ • uploads/      │
│ • POST /anonymize│               │ • samples/      │
│ • GET /status   │                │ • config/       │
└─────────────────┘                └─────────────────┘
```

## Key Takeaways

### ✅ Backend Handles:
- All data processing and anonymization
- File loading and memory optimization
- Background job processing
- API endpoints and routing
- Security and hashing algorithms

### ✅ Frontend Handles:
- User interface and experience
- File upload/download interface
- Configuration management
- API communication
- Progress display and feedback

### 🔄 Communication:
- RESTful API calls from frontend to backend
- JSON data exchange
- File transfer via HTTP multipart
- Real-time status updates

This architecture ensures **separation of concerns**, **scalability**, and **maintainability** while providing optimal performance for different file sizes and processing requirements.
