"""Integration tests for the complete data anonymization workflow."""

import pytest
import tempfile
import json
from pathlib import Path
import pandas as pd
import numpy as np
from io import StringIO
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_anonymizer.core.anonymizer import DataAnonymizer, run_anonymization_job
from data_anonymizer.utils.data_generator import SampleDataGenerator


class TestEndToEndWorkflow:
    """Test complete end-to-end anonymization workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        self.anonymizer = DataAnonymizer()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_csv_complete_workflow(self):
        """Test complete CSV anonymization workflow."""
        # Create test CSV file
        test_data = pd.DataFrame({
            'name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'email': ['john@example.com', 'jane@company.org', 'bob@test.net'],
            'phone': ['(555) 123-4567', '555-987-6543', '555.555.5555'],
            'age': [25, 35, 45],
            'salary': [50000, 75000, 90000],
            'department': ['IT', 'HR', 'Finance']
        })
        
        input_path = self.temp_dir / "test_input.csv"
        output_path = self.temp_dir / "test_output.csv"
        
        test_data.to_csv(input_path, index=False)
        
        # Define anonymization configuration
        config = {
            'Sheet1': {
                'name': 'hash',
                'email': 'anonymize_email',
                'phone': 'anonymize_phone',
                'age': {'method': 'generalize_numeric', 'options': {'bin_size': 10}},
                'salary': {'method': 'perturb', 'options': {'type': 'percentage', 'percentage': 10}},
                'department': {'method': 'substitute', 'options': {'type': 'generic'}}
            }
        }
        
        # Run anonymization
        run_anonymization_job(
            str(input_path),
            str(output_path),
            'csv',
            config
        )
        
        # Verify output
        assert output_path.exists()
        result_data = pd.read_csv(output_path)
        
        # Verify structure
        assert len(result_data) == len(test_data)
        assert set(result_data.columns) == set(test_data.columns)
        
        # Verify anonymization
        assert result_data['name'].iloc[0] != 'John Doe'
        assert '@' in result_data['email'].iloc[0]
        assert result_data['phone'].iloc[0] != '(555) 123-4567'
        assert '-' in result_data['age'].iloc[0]  # Should be generalized
        assert result_data['salary'].iloc[0] != 50000  # Should be perturbed

    def test_excel_multisheet_workflow(self):
        """Test complete Excel multi-sheet anonymization workflow."""
        # Create test Excel file with multiple sheets
        employees_data = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'email': ['john@company.com', 'jane@company.com', 'bob@company.com'],
            'department_id': [1, 2, 1]
        })
        
        departments_data = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['IT', 'HR', 'Finance'],
            'budget': [100000, 80000, 120000]
        })
        
        input_path = self.temp_dir / "test_multisheet.xlsx"
        output_path = self.temp_dir / "test_multisheet_output.xlsx"
        
        with pd.ExcelWriter(input_path) as writer:
            employees_data.to_excel(writer, sheet_name='Employees', index=False)
            departments_data.to_excel(writer, sheet_name='Departments', index=False)
        
        # Define configuration for multiple sheets
        config = {
            'Employees': {
                'name': 'hash',
                'email': 'anonymize_email',
                'department_id': 'hash'
            },
            'Departments': {
                'name': {'method': 'substitute', 'options': {'type': 'generic'}},
                'budget': {'method': 'perturb', 'options': {'type': 'percentage', 'percentage': 15}}
            }
        }
        
        # Run anonymization
        run_anonymization_job(
            str(input_path),
            str(output_path),
            'xlsx',
            config
        )
        
        # Verify output
        assert output_path.exists()
        result_sheets = pd.read_excel(output_path, sheet_name=None)
        
        # Verify structure
        assert 'Employees' in result_sheets
        assert 'Departments' in result_sheets
        assert len(result_sheets['Employees']) == len(employees_data)
        assert len(result_sheets['Departments']) == len(departments_data)
        
        # Verify anonymization
        emp_result = result_sheets['Employees']
        dept_result = result_sheets['Departments']
        
        assert emp_result['name'].iloc[0] != 'John Doe'
        assert '@' in emp_result['email'].iloc[0]
        assert dept_result['name'].iloc[0] != 'IT'
        assert dept_result['budget'].iloc[0] != 100000

    def test_large_dataset_workflow(self):
        """Test workflow with large dataset."""
        # Generate large dataset
        size = 10000
        large_data = pd.DataFrame({
            'id': range(size),
            'name': [f'Person_{i}' for i in range(size)],
            'email': [f'user{i}@company{i%100}.com' for i in range(size)],
            'age': np.random.randint(18, 80, size),
            'salary': np.random.randint(30000, 150000, size)
        })
        
        input_path = self.temp_dir / "large_dataset.csv"
        output_path = self.temp_dir / "large_dataset_output.csv"
        
        large_data.to_csv(input_path, index=False)
        
        config = {
            'Sheet1': {
                'name': 'hash',
                'email': 'anonymize_email',
                'age': {'method': 'generalize_numeric', 'options': {'bin_size': 5}},
                'salary': {'method': 'k_anonymity', 'options': {'k': 5}}
            }
        }
        
        # Run anonymization
        import time
        start_time = time.time()
        
        run_anonymization_job(
            str(input_path),
            str(output_path),
            'csv',
            config
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify output and performance
        assert output_path.exists()
        result_data = pd.read_csv(output_path)
        
        assert len(result_data) == size
        assert processing_time < 60  # Should complete within 1 minute
        
        # Verify anonymization quality
        assert result_data['name'].iloc[0] != 'Person_0'
        assert '@' in result_data['email'].iloc[0]
        assert '-' in result_data['age'].iloc[0]  # Generalized format

    def test_configuration_validation_workflow(self):
        """Test workflow with various configuration validations."""
        test_data = pd.DataFrame({
            'name': ['John Doe', 'Jane Smith'],
            'age': [25, 35],
            'email': ['john@example.com', 'jane@example.com']
        })
        
        input_path = self.temp_dir / "validation_test.csv"
        output_path = self.temp_dir / "validation_output.csv"
        
        test_data.to_csv(input_path, index=False)
        
        # Test with invalid method
        invalid_config = {
            'Sheet1': {
                'name': 'invalid_method',
                'age': 'generalize_numeric',
                'email': 'anonymize_email'
            }
        }
        
        # This should not crash but should fall back to default (hash)
        run_anonymization_job(
            str(input_path),
            str(output_path),
            'csv',
            invalid_config
        )
        
        assert output_path.exists()
        result_data = pd.read_csv(output_path)
        
        # Should have processed with fallback method
        assert len(result_data) == 2
        assert result_data['name'].iloc[0] != 'John Doe'

    def test_error_handling_workflow(self):
        """Test error handling in complete workflow."""
        # Test with non-existent input file
        with pytest.raises(FileNotFoundError):
            run_anonymization_job(
                "non_existent_file.csv",
                "output.csv",
                'csv',
                {'Sheet1': {'name': 'hash'}}
            )
        
        # Test with invalid output format
        test_data = pd.DataFrame({'name': ['John']})
        input_path = self.temp_dir / "error_test.csv"
        test_data.to_csv(input_path, index=False)
        
        with pytest.raises(ValueError):
            run_anonymization_job(
                str(input_path),
                str(self.temp_dir / "output.txt"),  # Invalid extension
                'txt',
                {'Sheet1': {'name': 'hash'}}
            )


class TestDataQualityPreservation:
    """Test that data quality is preserved through anonymization."""

    def setup_method(self):
        """Set up test fixtures."""
        self.anonymizer = DataAnonymizer()

    def test_data_type_preservation(self):
        """Test that data types are preserved where appropriate."""
        df = pd.DataFrame({
            'text_col': ['A', 'B', 'C'],
            'numeric_col': [1, 2, 3],
            'float_col': [1.1, 2.2, 3.3],
            'bool_col': [True, False, True]
        })
        
        # Apply methods that should preserve types
        config = {
            'text_col': 'hash',
            'numeric_col': {'method': 'perturb', 'options': {'type': 'uniform', 'range': 1}},
            'float_col': {'method': 'perturb', 'options': {'type': 'uniform', 'range': 0.1}},
            'bool_col': 'hash'
        }
        
        result = self.anonymizer.anonymize_dataframe(df, config)
        
        # Check that numeric columns maintain numeric types
        assert pd.api.types.is_numeric_dtype(result['numeric_col'])
        assert pd.api.types.is_numeric_dtype(result['float_col'])

    def test_statistical_properties_preservation(self):
        """Test that statistical properties are reasonably preserved."""
        # Create data with known statistical properties
        np.random.seed(42)
        df = pd.DataFrame({
            'values': np.random.normal(100, 15, 1000),
            'categories': np.random.choice(['A', 'B', 'C'], 1000)
        })
        
        original_mean = df['values'].mean()
        original_std = df['values'].std()
        original_cat_counts = df['categories'].value_counts()
        
        config = {
            'values': {'method': 'perturb', 'options': {'type': 'gaussian', 'range': 5}},
            'categories': {'method': 'k_anonymity', 'options': {'k': 50}}
        }
        
        result = self.anonymizer.anonymize_dataframe(df, config)
        
        # Check that statistical properties are reasonably preserved
        new_mean = result['values'].mean()
        new_std = result['values'].std()
        
        # Mean should be close (within 10% for this test)
        assert abs(new_mean - original_mean) / original_mean < 0.1
        
        # Standard deviation should be reasonably close
        assert abs(new_std - original_std) / original_std < 0.3

    def test_relationship_preservation(self):
        """Test that relationships between columns are preserved where intended."""
        # Create data with known relationships
        df = pd.DataFrame({
            'employee_id': [1, 2, 3, 4, 5],
            'department': ['IT', 'HR', 'IT', 'Finance', 'HR'],
            'salary': [80000, 60000, 85000, 75000, 65000],
            'manager_id': [1, 2, 1, 4, 2]  # Some employees manage others
        })
        
        # Use consistent hashing for related fields
        config = {
            'employee_id': 'hash',
            'department': {'method': 'substitute', 'options': {'type': 'generic'}},
            'salary': {'method': 'perturb', 'options': {'type': 'percentage', 'percentage': 5}},
            'manager_id': 'hash'  # Same method as employee_id
        }
        
        result = self.anonymizer.anonymize_dataframe(df, config)
        
        # Check that self-references are maintained
        # Employee 1 manages themselves and employee 3
        emp1_hash = result[result.index == 0]['employee_id'].iloc[0]
        emp3_manager_hash = result[result.index == 2]['manager_id'].iloc[0]
        
        assert emp1_hash == emp3_manager_hash

    def test_uniqueness_preservation(self):
        """Test that uniqueness constraints are preserved."""
        df = pd.DataFrame({
            'unique_id': [1, 2, 3, 4, 5],
            'email': ['a@test.com', 'b@test.com', 'c@test.com', 'd@test.com', 'e@test.com'],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve']
        })
        
        config = {
            'unique_id': 'hash',
            'email': 'anonymize_email',
            'name': 'hash'
        }
        
        result = self.anonymizer.anonymize_dataframe(df, config)
        
        # Check that all anonymized values are still unique
        assert len(result['unique_id'].unique()) == len(df['unique_id'].unique())
        assert len(result['email'].unique()) == len(df['email'].unique())
        assert len(result['name'].unique()) == len(df['name'].unique())


class TestRealWorldScenarios:
    """Test real-world anonymization scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.anonymizer = DataAnonymizer()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_healthcare_data_scenario(self):
        """Test anonymization of healthcare-like data."""
        healthcare_data = pd.DataFrame({
            'patient_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
            'name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Davis'],
            'ssn': ['123-45-6789', '987-65-4321', '456-78-9012', '789-01-2345', '321-54-9876'],
            'date_of_birth': ['1985-03-15', '1990-07-22', '1978-11-08', '1992-01-30', '1980-05-14'],
            'diagnosis': ['Diabetes', 'Hypertension', 'Asthma', 'Diabetes', 'Hypertension'],
            'treatment_cost': [5000, 3000, 2000, 5500, 3200],
            'zip_code': ['12345', '67890', '54321', '98765', '13579']
        })
        
        # HIPAA-compliant anonymization
        config = {
            'Sheet1': {
                'patient_id': 'hash',
                'name': 'hash',
                'ssn': 'hash',
                'date_of_birth': {'method': 'generalize_date', 'options': {'granularity': 'year'}},
                'diagnosis': 'hash',
                'treatment_cost': {'method': 'generalize_numeric', 'options': {'bin_size': 1000}},
                'zip_code': {'method': 'generalize_numeric', 'options': {'bin_size': 10000}}
            }
        }
        
        input_path = self.temp_dir / "healthcare.csv"
        output_path = self.temp_dir / "healthcare_anonymized.csv"
        
        healthcare_data.to_csv(input_path, index=False)
        
        run_anonymization_job(
            str(input_path),
            str(output_path),
            'csv',
            config
        )
        
        result = pd.read_csv(output_path)
        
        # Verify HIPAA compliance
        assert result['name'].iloc[0] != 'John Doe'
        assert result['ssn'].iloc[0] != '123-45-6789'
        # Test that date is generalized to year format
        assert result['date_of_birth'].iloc[0] == 1985 or result['date_of_birth'].iloc[0] == '1985'  # Both formats acceptable
        assert result['diagnosis'].iloc[0] != 'Diabetes'
        assert '-' in result['treatment_cost'].iloc[0]  # Generalized
        assert result['zip_code'].iloc[0] != '12345'  # Generalized

    def test_financial_data_scenario(self):
        """Test anonymization of financial data."""
        financial_data = pd.DataFrame({
            'account_id': ['ACC001', 'ACC002', 'ACC003', 'ACC004'],
            'customer_name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown'],
            'account_balance': [15000.50, 25000.75, 8000.25, 45000.00],
            'transaction_amount': [500.00, 1200.50, 300.75, 2000.00],
            'credit_score': [750, 680, 720, 800],
            'branch_code': ['BR001', 'BR002', 'BR001', 'BR003']
        })
        
        # Financial services anonymization
        config = {
            'Sheet1': {
                'account_id': 'hash',
                'customer_name': 'hash',
                'account_balance': {'method': 'perturb', 'options': {'type': 'percentage', 'percentage': 10}},
                'transaction_amount': {'method': 'perturb', 'options': {'type': 'percentage', 'percentage': 15}},
                'credit_score': {'method': 'generalize_numeric', 'options': {'bin_size': 50}},
                'branch_code': 'hash'
            }
        }
        
        input_path = self.temp_dir / "financial.csv"
        output_path = self.temp_dir / "financial_anonymized.csv"
        
        financial_data.to_csv(input_path, index=False)
        
        run_anonymization_job(
            str(input_path),
            str(output_path),
            'csv',
            config
        )
        
        result = pd.read_csv(output_path)
        
        # Verify financial data anonymization
        assert result['account_id'].iloc[0] != 'ACC001'
        assert result['customer_name'].iloc[0] != 'John Doe'
        assert result['account_balance'].iloc[0] != 15000.50
        assert result['transaction_amount'].iloc[0] != 500.00
        assert '-' in result['credit_score'].iloc[0]  # Generalized
        assert result['branch_code'].iloc[0] != 'BR001'

    def test_hr_data_scenario(self):
        """Test anonymization of HR data."""
        hr_data = pd.DataFrame({
            'employee_id': ['E001', 'E002', 'E003', 'E004', 'E005'],
            'full_name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Davis'],
            'email': ['john@company.com', 'jane@company.com', 'bob@company.com', 'alice@company.com', 'charlie@company.com'],
            'phone': ['555-1234', '555-5678', '555-9012', '555-3456', '555-7890'],
            'salary': [75000, 85000, 65000, 95000, 70000],
            'hire_date': ['2020-01-15', '2019-03-22', '2021-07-10', '2018-11-05', '2022-02-28'],
            'department': ['Engineering', 'Marketing', 'Engineering', 'Sales', 'HR'],
            'performance_rating': [4.2, 3.8, 4.5, 3.9, 4.1]
        })
        
        # HR anonymization preserving some analytics capability
        config = {
            'Sheet1': {
                'employee_id': 'hash',
                'full_name': 'hash',
                'email': 'anonymize_email',
                'phone': 'anonymize_phone',
                'salary': {'method': 'generalize_numeric', 'options': {'bin_size': 10000}},
                'hire_date': {'method': 'generalize_date', 'options': {'granularity': 'quarter'}},
                'department': {'method': 'substitute', 'options': {'type': 'generic'}},
                'performance_rating': {'method': 'perturb', 'options': {'type': 'uniform', 'range': 0.2}}
            }
        }
        
        input_path = self.temp_dir / "hr_data.csv"
        output_path = self.temp_dir / "hr_anonymized.csv"
        
        hr_data.to_csv(input_path, index=False)
        
        run_anonymization_job(
            str(input_path),
            str(output_path),
            'csv',
            config
        )
        
        result = pd.read_csv(output_path)
        
        # Verify HR data anonymization
        assert result['employee_id'].iloc[0] != 'E001'
        assert result['full_name'].iloc[0] != 'John Doe'
        assert '@' in result['email'].iloc[0]
        assert result['phone'].iloc[0] != '555-1234'
        assert '-' in result['salary'].iloc[0]  # Generalized
        assert 'Q' in result['hire_date'].iloc[0]  # Quarter format
        assert result['department'].iloc[0] != 'Engineering' or result['department'].iloc[0] == '[REDACTED]'


class TestSampleDataGeneration:
    """Test sample data generation integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.generator = SampleDataGenerator(str(self.temp_dir))

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sample_data_generation_and_anonymization(self):
        """Test generating sample data and then anonymizing it."""
        # Generate sample CSV
        sample_path = self.generator.generate_csv_sample("test_sample.csv", rows=100)
        
        # Verify sample was created
        assert sample_path.exists()
        
        # Load and verify sample data
        sample_data = pd.read_csv(sample_path)
        assert len(sample_data) == 100
        assert 'Name' in sample_data.columns
        assert 'Email' in sample_data.columns
        assert 'Phone' in sample_data.columns
        
        # Anonymize the sample data
        config = {
            'Sheet1': {
                'Name': 'hash',
                'Email': 'anonymize_email',
                'Phone': 'anonymize_phone',
                'Age': {'method': 'generalize_numeric', 'options': {'bin_size': 10}},
                'Salary': {'method': 'perturb', 'options': {'type': 'percentage', 'percentage': 10}}
            }
        }
        
        output_path = self.temp_dir / "anonymized_sample.csv"
        
        run_anonymization_job(
            str(sample_path),
            str(output_path),
            'csv',
            config
        )
        
        # Verify anonymized output
        result = pd.read_csv(output_path)
        assert len(result) == 100
        assert result['Name'].iloc[0] != sample_data['Name'].iloc[0]
        assert '@' in result['Email'].iloc[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
