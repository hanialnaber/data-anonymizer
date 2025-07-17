"""Test configuration and fixtures for the test suite."""

import pytest
import tempfile
from pathlib import Path
import os
import sys

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test configuration
@pytest.fixture(scope="session")
def test_config():
    """Test configuration settings."""
    return {
        "test_salt": "test_salt_12345",
        "sample_size": 100,
        "temp_dir": tempfile.gettempdir()
    }

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def sample_csv_data():
    """Sample CSV data for testing."""
    return {
        'name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
        'email': ['john.doe@example.com', 'jane.smith@company.org', 'bob.johnson@test.net'],
        'phone': ['(555) 123-4567', '555-987-6543', '555.555.5555'],
        'ssn': ['123-45-6789', '987-65-4321', '555-55-5555'],
        'age': [25, 35, 45],
        'salary': [50000, 75000, 90000],
        'hire_date': ['2020-01-15', '2019-03-20', '2021-07-10'],
        'department': ['Engineering', 'Marketing', 'Engineering']
    }

@pytest.fixture
def sample_excel_data():
    """Sample Excel data with multiple sheets."""
    return {
        'Employees': {
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'department': ['HR', 'IT', 'Finance']
        },
        'Departments': {
            'dept_id': [1, 2, 3],
            'dept_name': ['HR', 'IT', 'Finance'],
            'budget': [100000, 200000, 150000]
        }
    }

@pytest.fixture
def privacy_test_data():
    """Data specifically for privacy testing."""
    return {
        'personal_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
        'credit_card': ['1234-5678-9012-3456', '2345-6789-0123-4567', '3456-7890-1234-5678', '4567-8901-2345-6789', '5678-9012-3456-7890'],
        'medical_record': ['MR001', 'MR002', 'MR003', 'MR004', 'MR005'],
        'income': [45000, 55000, 65000, 75000, 85000],
        'diagnosis': ['Diabetes', 'Hypertension', 'Diabetes', 'Healthy', 'Hypertension']
    }
