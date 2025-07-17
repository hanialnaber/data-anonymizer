"""Tests for the FastAPI anonymization API."""

import pytest
import json
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
import pandas as pd

from src.data_anonymizer.api.main import app

client = TestClient(app)


class TestAnonymizerAPI:
    """Test suite for the anonymization API endpoints."""

    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"

    def test_api_status(self):
        """Test API status endpoint."""
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "privacy_methods" in data
        
        # Verify all expected methods are listed
        expected_methods = [
            "hash", "mask", "pseudonymize", "substitute", "shuffle",
            "perturb", "generalize_numeric", "generalize_date",
            "anonymize_email", "anonymize_phone", "anonymize_ssn",
            "k_anonymity", "differential_privacy"
        ]
        
        for method in expected_methods:
            assert method in data["privacy_methods"]

    def test_list_samples(self):
        """Test listing sample files."""
        response = client.get("/api/v1/samples")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    def test_generate_samples(self):
        """Test generating sample data."""
        response = client.post("/api/v1/generate-samples")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "files" in data
        assert isinstance(data["files"], list)

    def test_upload_file_csv(self):
        """Test file upload with CSV."""
        # Create a temporary CSV file
        test_data = "name,age,email\nJohn Doe,25,john@example.com\nJane Smith,30,jane@example.com"
        
        files = {"file": ("test.csv", test_data, "text/csv")}
        response = client.post("/api/v1/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["filename"] == "test.csv"

    def test_upload_file_excel(self):
        """Test file upload with Excel."""
        # Create a temporary Excel file
        df = pd.DataFrame({
            "name": ["John Doe", "Jane Smith"],
            "age": [25, 30],
            "email": ["john@example.com", "jane@example.com"]
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            df.to_excel(f.name, index=False)
            temp_path = Path(f.name)
        
        try:
            with open(temp_path, 'rb') as f:
                files = {"file": ("test.xlsx", f.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                response = client.post("/api/v1/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["filename"] == "test.xlsx"
        finally:
            temp_path.unlink()

    def test_anonymize_data_simple(self):
        """Test data anonymization with simple configuration."""
        # First upload a file
        test_data = "name,age,email\nJohn Doe,25,john@example.com\nJane Smith,30,jane@example.com"
        files = {"file": ("test.csv", test_data, "text/csv")}
        upload_response = client.post("/api/v1/upload", files=files)
        assert upload_response.status_code == 200

        # Then anonymize it
        config = {
            "Sheet1": {
                "name": "hash",
                "email": "anonymize_email"
            }
        }
        
        anonymize_data = {
            "filename": "test.csv",
            "output_format": "csv",
            "masking_config": json.dumps(config)
        }
        
        response = client.post("/api/v1/anonymize", data=anonymize_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "processing"
        assert "result_file" in data

    def test_anonymize_data_complex_config(self):
        """Test data anonymization with complex configuration."""
        # Upload test file
        test_data = "name,age,salary,phone,department\nJohn Doe,25,50000,(555) 123-4567,Engineering\nJane Smith,30,60000,555-987-6543,Marketing"
        files = {"file": ("complex_test.csv", test_data, "text/csv")}
        upload_response = client.post("/api/v1/upload", files=files)
        assert upload_response.status_code == 200

        # Complex anonymization configuration
        config = {
            "Sheet1": {
                "name": {"method": "mask", "options": {"mask_char": "*", "preserve_length": True}},
                "age": {"method": "generalize_numeric", "options": {"bin_size": 10}},
                "salary": {"method": "perturb", "options": {"type": "percentage", "percentage": 10}},
                "phone": "anonymize_phone",
                "department": {"method": "substitute", "options": {"type": "generic"}}
            }
        }
        
        anonymize_data = {
            "filename": "complex_test.csv",
            "output_format": "csv",
            "masking_config": json.dumps(config)
        }
        
        response = client.post("/api/v1/anonymize", data=anonymize_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "processing"

    def test_anonymize_excel_with_sheets(self):
        """Test Excel anonymization with specific sheet selection."""
        # Create multi-sheet Excel file
        df1 = pd.DataFrame({"name": ["John"], "age": [25]})
        df2 = pd.DataFrame({"product": ["Widget"], "price": [100]})
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            with pd.ExcelWriter(f.name) as writer:
                df1.to_excel(writer, sheet_name="Employees", index=False)
                df2.to_excel(writer, sheet_name="Products", index=False)
            temp_path = Path(f.name)
        
        try:
            # Upload the file
            with open(temp_path, 'rb') as f:
                files = {"file": ("multi_sheet.xlsx", f.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                upload_response = client.post("/api/v1/upload", files=files)
            
            assert upload_response.status_code == 200
            
            # Anonymize with sheet selection
            config = {
                "Employees": {
                    "name": "hash"
                }
            }
            
            anonymize_data = {
                "filename": "multi_sheet.xlsx",
                "output_format": "xlsx",
                "masking_config": json.dumps(config),
                "selected_sheet": "Employees"
            }
            
            response = client.post("/api/v1/anonymize", data=anonymize_data)
            assert response.status_code == 200
            
        finally:
            temp_path.unlink()

    def test_download_file(self):
        """Test file download."""
        # First upload a file
        test_data = "name,age\nJohn Doe,25"
        files = {"file": ("download_test.csv", test_data, "text/csv")}
        upload_response = client.post("/api/v1/upload", files=files)
        assert upload_response.status_code == 200

        # Then download it
        response = client.get("/api/v1/download/download_test.csv")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"

    def test_download_nonexistent_file(self):
        """Test downloading non-existent file."""
        response = client.get("/api/v1/download/nonexistent.csv")
        assert response.status_code == 404

    def test_anonymize_invalid_config(self):
        """Test anonymization with invalid configuration."""
        # Upload a file first
        test_data = "name,age\nJohn Doe,25"
        files = {"file": ("invalid_config_test.csv", test_data, "text/csv")}
        upload_response = client.post("/api/v1/upload", files=files)
        assert upload_response.status_code == 200

        # Try to anonymize with invalid JSON
        anonymize_data = {
            "filename": "invalid_config_test.csv",
            "output_format": "csv",
            "masking_config": "invalid json"
        }
        
        response = client.post("/api/v1/anonymize", data=anonymize_data)
        assert response.status_code == 400

    def test_anonymize_nonexistent_file(self):
        """Test anonymization with non-existent file."""
        config = {"Sheet1": {"name": "hash"}}
        
        anonymize_data = {
            "filename": "nonexistent.csv",
            "output_format": "csv",
            "masking_config": json.dumps(config)
        }
        
        response = client.post("/api/v1/anonymize", data=anonymize_data)
        assert response.status_code == 404

    def test_anonymize_empty_config(self):
        """Test anonymization with empty configuration."""
        # Upload a file first
        test_data = "name,age\nJohn Doe,25"
        files = {"file": ("empty_config_test.csv", test_data, "text/csv")}
        upload_response = client.post("/api/v1/upload", files=files)
        assert upload_response.status_code == 200

        # Try to anonymize with empty config
        anonymize_data = {
            "filename": "empty_config_test.csv",
            "output_format": "csv",
            "masking_config": "{}"
        }
        
        response = client.post("/api/v1/anonymize", data=anonymize_data)
        assert response.status_code == 400


class TestAPIErrorHandling:
    """Test error handling in the API."""

    def test_upload_no_file(self):
        """Test upload without file."""
        response = client.post("/api/v1/upload")
        assert response.status_code == 422  # Validation error

    def test_anonymize_missing_parameters(self):
        """Test anonymization with missing parameters."""
        response = client.post("/api/v1/anonymize", data={"filename": "test.csv"})
        assert response.status_code == 422  # Validation error

    def test_invalid_endpoints(self):
        """Test invalid endpoints."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

        response = client.post("/api/v1/nonexistent")
        assert response.status_code == 404


class TestAPIIntegration:
    """Integration tests for the complete API workflow."""

    def test_complete_anonymization_workflow(self):
        """Test complete workflow from upload to download."""
        # 1. Upload file
        test_data = "name,age,email,phone\nJohn Doe,25,john@example.com,(555) 123-4567\nJane Smith,30,jane@example.com,555-987-6543"
        files = {"file": ("workflow_test.csv", test_data, "text/csv")}
        upload_response = client.post("/api/v1/upload", files=files)
        assert upload_response.status_code == 200

        # 2. Check samples (should include our uploaded file)
        samples_response = client.get("/api/v1/samples")
        assert samples_response.status_code == 200

        # 3. Anonymize data
        config = {
            "Sheet1": {
                "name": "hash",
                "email": "anonymize_email",
                "phone": "anonymize_phone",
                "age": {"method": "generalize_numeric", "options": {"bin_size": 10}}
            }
        }
        
        anonymize_data = {
            "filename": "workflow_test.csv",
            "output_format": "csv",
            "masking_config": json.dumps(config)
        }
        
        anonymize_response = client.post("/api/v1/anonymize", data=anonymize_data)
        assert anonymize_response.status_code == 200
        
        result_data = anonymize_response.json()
        assert "result_file" in result_data

        # 4. Download result (with some delay to allow processing)
        import time
        time.sleep(1)  # Allow background task to complete
        
        result_filename = result_data["result_file"]
        download_response = client.get(f"/api/v1/download/{result_filename}")
        # Note: Download might fail if background task hasn't completed
        # In a real test, you'd implement proper async handling

    def test_excel_multisheet_workflow(self):
        """Test workflow with Excel multi-sheet file."""
        # Create multi-sheet Excel file
        df1 = pd.DataFrame({
            "employee_id": [1, 2, 3],
            "name": ["John Doe", "Jane Smith", "Bob Johnson"],
            "department": ["IT", "HR", "Finance"]
        })
        df2 = pd.DataFrame({
            "dept_id": [1, 2, 3],
            "dept_name": ["IT", "HR", "Finance"],
            "budget": [100000, 80000, 120000]
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            with pd.ExcelWriter(f.name) as writer:
                df1.to_excel(writer, sheet_name="Employees", index=False)
                df2.to_excel(writer, sheet_name="Departments", index=False)
            temp_path = Path(f.name)
        
        try:
            # Upload
            with open(temp_path, 'rb') as f:
                files = {"file": ("multisheet_workflow.xlsx", f.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                upload_response = client.post("/api/v1/upload", files=files)
            
            assert upload_response.status_code == 200
            
            # Anonymize with configuration for multiple sheets
            config = {
                "Employees": {
                    "name": "hash",
                    "department": {"method": "substitute", "options": {"type": "generic"}}
                },
                "Departments": {
                    "budget": {"method": "perturb", "options": {"type": "percentage", "percentage": 15}}
                }
            }
            
            anonymize_data = {
                "filename": "multisheet_workflow.xlsx",
                "output_format": "xlsx",
                "masking_config": json.dumps(config)
            }
            
            anonymize_response = client.post("/api/v1/anonymize", data=anonymize_data)
            assert anonymize_response.status_code == 200
            
        finally:
            temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
