"""Comprehensive tests for DataAnonymizer class."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import re
from pathlib import Path
import tempfile
import json

from src.data_anonymizer.core.anonymizer import DataAnonymizer


class TestDataAnonymizer:
    """Test suite for DataAnonymizer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.anonymizer = DataAnonymizer(salt="test_salt")
        
        # Create test data
        self.test_data = pd.DataFrame({
            'name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'email': ['john.doe@example.com', 'jane.smith@company.org', 'bob.johnson@test.net'],
            'phone': ['(555) 123-4567', '555-987-6543', '555.555.5555'],
            'ssn': ['123-45-6789', '987-65-4321', '555-55-5555'],
            'age': [25, 35, 45],
            'salary': [50000, 75000, 90000],
            'hire_date': ['2020-01-15', '2019-03-20', '2021-07-10'],
            'department': ['Engineering', 'Marketing', 'Engineering']
        })

    def test_hash_value_consistency(self):
        """Test that hash values are consistent with same salt."""
        value = "test_value"
        hash1 = self.anonymizer.hash_value(value)
        hash2 = self.anonymizer.hash_value(value)
        
        assert hash1 == hash2, "Hash values should be consistent"
        assert len(hash1) == 64, "SHA256 hash should be 64 characters"

    def test_hash_value_different_algorithms(self):
        """Test different hash algorithms."""
        value = "test_value"
        
        sha256_hash = self.anonymizer.hash_value(value, "sha256")
        sha512_hash = self.anonymizer.hash_value(value, "sha512")
        md5_hash = self.anonymizer.hash_value(value, "md5")
        
        assert len(sha256_hash) == 64
        assert len(sha512_hash) == 128
        assert len(md5_hash) == 32
        
        # All should be different
        assert sha256_hash != sha512_hash != md5_hash

    def test_mask_value_preserve_length(self):
        """Test masking with length preservation."""
        value = "sensitive_data"
        masked = self.anonymizer.mask_value(value, "*", True)
        
        assert len(masked) == len(value)
        assert all(c == "*" for c in masked)

    def test_mask_value_show_boundaries(self):
        """Test masking showing first and last character."""
        value = "sensitive_data"
        masked = self.anonymizer.mask_value(value, "*", False)
        
        assert masked.startswith("s")
        assert masked.endswith("a")
        assert "*" in masked

    def test_pseudonymize_value_consistency(self):
        """Test pseudonymization consistency."""
        value = "John Doe"
        pseudo1 = self.anonymizer.pseudonymize_value(value)
        pseudo2 = self.anonymizer.pseudonymize_value(value)
        
        assert pseudo1 == pseudo2, "Pseudonyms should be consistent"
        assert pseudo1.startswith("ID_"), "Pseudonym should have correct prefix"

    def test_generalize_numeric_binning(self):
        """Test numeric generalization with different bin sizes."""
        # Test with default bin size (10)
        result = self.anonymizer.generalize_numeric(25)
        assert result == "20-29"
        
        # Test with custom bin size
        result = self.anonymizer.generalize_numeric(25, bin_size=5)
        assert result == "25-29"
        
        # Test with non-numeric value
        result = self.anonymizer.generalize_numeric("not_a_number")
        assert result == "not_a_number"

    def test_generalize_date_granularity(self):
        """Test date generalization with different granularities."""
        date_str = "2023-05-15"
        
        # Test year granularity
        result = self.anonymizer.generalize_date(date_str, "year")
        assert result == "2023"
        
        # Test month granularity
        result = self.anonymizer.generalize_date(date_str, "month")
        assert result == "2023-05"
        
        # Test quarter granularity
        result = self.anonymizer.generalize_date(date_str, "quarter")
        assert result == "2023-Q2"

    def test_anonymize_email_domain_preservation(self):
        """Test email anonymization with domain preservation."""
        # Test with common domain (should be preserved)
        email = "user@gmail.com"
        result = self.anonymizer.anonymize_email(email)
        assert "@gmail.com" in result
        assert result.startswith("user") and result != email  # Should be anonymized but start with user
        
        # Test with custom domain (should be anonymized)
        email = "user@company.com"
        result = self.anonymizer.anonymize_email(email)
        assert "@company.com" not in result
        assert "@" in result

    def test_anonymize_phone_format_preservation(self):
        """Test phone number anonymization with format preservation."""
        # Test different phone formats
        phone_formats = [
            "(555) 123-4567",
            "555-123-4567",
            "555.123.4567",
            "5551234567"
        ]
        
        for phone in phone_formats:
            result = self.anonymizer.anonymize_phone(phone)
            
            # Should preserve non-digit characters
            original_pattern = re.sub(r'\d', 'X', phone)
            result_pattern = re.sub(r'\d', 'X', result)
            assert original_pattern == result_pattern

    def test_anonymize_ssn_format_preservation(self):
        """Test SSN anonymization with format preservation."""
        # Test with dashes
        ssn = "123-45-6789"
        result = self.anonymizer.anonymize_ssn(ssn)
        assert re.match(r'\d{3}-\d{2}-\d{4}', result)
        assert result != ssn
        
        # Test without dashes
        ssn = "123456789"
        result = self.anonymizer.anonymize_ssn(ssn)
        assert re.match(r'\d{9}', result)
        assert result != ssn

    def test_k_anonymity_suppression(self):
        """Test k-anonymity suppression."""
        # Create test series with varying frequencies
        test_series = pd.Series(['A', 'A', 'A', 'B', 'B', 'C'])
        
        # Test with k=3 (only 'A' appears 3+ times)
        result = self.anonymizer.k_anonymity_suppress(test_series, k=3)
        
        # 'A' should remain, 'B' and 'C' should be suppressed
        assert all(result[result == 'A'].index == [0, 1, 2])
        assert all(result[result == '[SUPPRESSED]'].index == [3, 4, 5])

    def test_differential_privacy_noise(self):
        """Test differential privacy noise addition."""
        value = 100
        epsilon = 1.0
        
        # Test multiple times to ensure noise is added
        results = [self.anonymizer.differential_privacy_noise(value, epsilon) for _ in range(10)]
        
        # Should have some variation
        assert len(set(results)) > 1, "Results should vary due to noise"
        
        # All results should be numeric
        assert all(isinstance(r, (int, float)) for r in results)

    def test_perturb_value_uniform_noise(self):
        """Test value perturbation with uniform noise."""
        value = 100
        config = {"type": "uniform", "range": 10}
        
        results = [self.anonymizer.perturb_value(value, config) for _ in range(10)]
        
        # Should all be within expected range
        assert all(90 <= r <= 110 for r in results)
        
        # Should have variation
        assert len(set(results)) > 1

    def test_perturb_value_gaussian_noise(self):
        """Test value perturbation with Gaussian noise."""
        value = 100
        config = {"type": "gaussian", "range": 5}
        
        results = [self.anonymizer.perturb_value(value, config) for _ in range(10)]
        
        # Should have variation
        assert len(set(results)) > 1
        
        # Should be numeric
        assert all(isinstance(r, (int, float)) for r in results)

    def test_perturb_value_percentage_noise(self):
        """Test value perturbation with percentage-based noise."""
        value = 100
        config = {"type": "percentage", "percentage": 10}
        
        results = [self.anonymizer.perturb_value(value, config) for _ in range(10)]
        
        # Should all be within 10% of original
        assert all(90 <= r <= 110 for r in results)

    def test_substitute_value_with_list(self):
        """Test value substitution with custom list."""
        config = {"list": ["Apple", "Banana", "Cherry"]}
        
        results = [self.anonymizer.substitute_value("original", config) for _ in range(10)]
        
        # All results should be from the provided list
        assert all(r in config["list"] for r in results)

    def test_substitute_value_with_type(self):
        """Test value substitution with data type."""
        config = {"type": "names"}
        
        result = self.anonymizer.substitute_value("original", config)
        
        # Should be from the names list
        assert result in self.anonymizer.substitution_lists["names"]

    def test_shuffle_column(self):
        """Test column shuffling."""
        original_series = pd.Series([1, 2, 3, 4, 5])
        shuffled = self.anonymizer.shuffle_column(original_series)
        
        # Should contain same values
        assert set(shuffled) == set(original_series)
        
        # Should preserve data types
        assert shuffled.dtype == original_series.dtype

    def test_anonymize_dataframe_hash_method(self):
        """Test DataFrame anonymization with hash method."""
        config = {"name": "hash"}
        
        result = self.anonymizer.anonymize_dataframe(self.test_data, config)
        
        # Original data should be unchanged
        assert self.test_data.loc[0, 'name'] == 'John Doe'
        
        # Result should be hashed
        assert result.loc[0, 'name'] != 'John Doe'
        assert len(result.loc[0, 'name']) == 64  # SHA256 length

    def test_anonymize_dataframe_mask_method(self):
        """Test DataFrame anonymization with mask method."""
        config = {"name": {"method": "mask", "options": {"mask_char": "*"}}}
        
        result = self.anonymizer.anonymize_dataframe(self.test_data, config)
        
        # Should be masked
        assert all("*" in name for name in result['name'])

    def test_anonymize_dataframe_multiple_methods(self):
        """Test DataFrame anonymization with multiple methods."""
        config = {
            "name": "hash",
            "email": "anonymize_email",
            "phone": "anonymize_phone",
            "age": {"method": "generalize_numeric", "options": {"bin_size": 10}}
        }
        
        result = self.anonymizer.anonymize_dataframe(self.test_data, config)
        
        # Check each method was applied
        assert len(result.loc[0, 'name']) == 64  # Hash
        assert "@" in result.loc[0, 'email'] and result.loc[0, 'email'] != self.test_data.loc[0, 'email']
        assert result.loc[0, 'phone'] != self.test_data.loc[0, 'phone']
        assert "-" in result.loc[0, 'age']  # Generalized format

    def test_anonymize_dataframe_remove_column(self):
        """Test DataFrame anonymization with column removal."""
        config = {"ssn": "remove"}
        
        result = self.anonymizer.anonymize_dataframe(self.test_data, config)
        
        # SSN column should be removed
        assert "ssn" not in result.columns
        assert "ssn" in self.test_data.columns  # Original unchanged

    def test_load_data_csv(self):
        """Test loading CSV data."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            self.test_data.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            result = self.anonymizer.load_data(temp_path)
            
            assert "Sheet1" in result
            pd.testing.assert_frame_equal(result["Sheet1"], self.test_data)
        finally:
            Path(temp_path).unlink()

    def test_load_data_excel(self):
        """Test loading Excel data."""
        # Create temporary Excel file
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            self.test_data.to_excel(f.name, index=False, sheet_name="TestSheet")
            temp_path = f.name
        
        try:
            result = self.anonymizer.load_data(temp_path)
            
            assert "TestSheet" in result
            # Compare without index since Excel loading might affect it
            pd.testing.assert_frame_equal(result["TestSheet"], self.test_data, check_dtype=False)
        finally:
            Path(temp_path).unlink()

    def test_save_data_csv(self):
        """Test saving data to CSV."""
        data = {"Sheet1": self.test_data}
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        try:
            self.anonymizer.save_data(data, temp_path)
            
            # Verify file was created and contains correct data
            loaded_data = pd.read_csv(temp_path)
            pd.testing.assert_frame_equal(loaded_data, self.test_data, check_dtype=False)
        finally:
            Path(temp_path).unlink()

    def test_save_data_excel(self):
        """Test saving data to Excel."""
        data = {"Sheet1": self.test_data, "Sheet2": self.test_data}
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            temp_path = f.name
        
        try:
            self.anonymizer.save_data(data, temp_path)
            
            # Verify file was created and contains correct data
            loaded_data = pd.read_excel(temp_path, sheet_name=None)
            assert "Sheet1" in loaded_data
            assert "Sheet2" in loaded_data
        finally:
            Path(temp_path).unlink()

    def test_edge_cases_empty_values(self):
        """Test handling of empty/null values."""
        # Test with None values
        assert self.anonymizer.hash_value(None) is not None
        assert self.anonymizer.mask_value(None) is not None
        
        # Test with empty strings
        assert self.anonymizer.hash_value("") is not None
        assert self.anonymizer.mask_value("") == ""

    def test_edge_cases_invalid_inputs(self):
        """Test handling of invalid inputs."""
        # Test invalid phone numbers
        invalid_phones = ["", "abc", "123"]
        for phone in invalid_phones:
            result = self.anonymizer.anonymize_phone(phone)
            assert result == phone or isinstance(result, str)
        
        # Test invalid emails
        invalid_emails = ["not_an_email", "", "test@"]
        for email in invalid_emails:
            result = self.anonymizer.anonymize_email(email)
            assert isinstance(result, str)

    def test_privacy_preservation_properties(self):
        """Test that privacy preservation properties are maintained."""
        # Test that hashing is deterministic
        value = "test_value"
        hash1 = self.anonymizer.hash_value(value)
        hash2 = self.anonymizer.hash_value(value)
        assert hash1 == hash2
        
        # Test that different values produce different hashes
        value2 = "different_value"
        hash3 = self.anonymizer.hash_value(value2)
        assert hash1 != hash3
        
        # Test that format preservation maintains utility
        phone = "(555) 123-4567"
        anon_phone = self.anonymizer.anonymize_phone(phone)
        assert len(phone) == len(anon_phone)
        assert phone.count("(") == anon_phone.count("(")
        assert phone.count(")") == anon_phone.count(")")
        assert phone.count("-") == anon_phone.count("-")
        assert phone.count(" ") == anon_phone.count(" ")

    def test_anonymization_quality_metrics(self):
        """Test quality metrics for anonymization."""
        # Test uniqueness preservation
        original_names = ["John", "Jane", "Bob", "Alice"]
        df = pd.DataFrame({"name": original_names})
        
        config = {"name": "hash"}
        result = self.anonymizer.anonymize_dataframe(df, config)
        
        # Should preserve uniqueness
        assert len(result["name"].unique()) == len(df["name"].unique())
        
        # Test data type preservation where applicable
        numeric_df = pd.DataFrame({"age": [25, 30, 35, 40]})
        config = {"age": {"method": "perturb", "options": {"type": "uniform", "range": 5}}}
        result = self.anonymizer.anonymize_dataframe(numeric_df, config)
        
        # Should preserve numeric type
        assert pd.api.types.is_numeric_dtype(result["age"])


class TestAnonymizationMethods:
    """Test individual anonymization methods in detail."""

    def setup_method(self):
        """Set up test fixtures."""
        self.anonymizer = DataAnonymizer(salt="test_salt")

    @pytest.mark.parametrize("algorithm", ["sha256", "sha512", "md5"])
    def test_hash_algorithms(self, algorithm):
        """Test all supported hash algorithms."""
        value = "test_value"
        result = self.anonymizer.hash_value(value, algorithm)
        
        expected_lengths = {"sha256": 64, "sha512": 128, "md5": 32}
        assert len(result) == expected_lengths[algorithm]
        
        # Test consistency
        assert result == self.anonymizer.hash_value(value, algorithm)

    @pytest.mark.parametrize("granularity,expected_format", [
        ("year", r"^\d{4}$"),
        ("month", r"^\d{4}-\d{2}$"),
        ("quarter", r"^\d{4}-Q[1-4]$"),
    ])
    def test_date_generalization_formats(self, granularity, expected_format):
        """Test date generalization with different formats."""
        date_str = "2023-05-15"
        result = self.anonymizer.generalize_date(date_str, granularity)
        assert re.match(expected_format, result)

    @pytest.mark.parametrize("bin_size,value,expected", [
        (10, 25, "20-29"),
        (5, 23, "20-24"),
        (100, 150, "100-199"),
    ])
    def test_numeric_generalization_bins(self, bin_size, value, expected):
        """Test numeric generalization with different bin sizes."""
        result = self.anonymizer.generalize_numeric(value, bin_size)
        assert result == expected

    @pytest.mark.parametrize("epsilon", [0.1, 0.5, 1.0, 2.0])
    def test_differential_privacy_epsilon_values(self, epsilon):
        """Test differential privacy with different epsilon values."""
        value = 100
        results = [self.anonymizer.differential_privacy_noise(value, epsilon) for _ in range(10)]
        
        # Should have variation
        assert len(set(results)) > 1
        
        # Higher epsilon should generally result in less noise (more accuracy)
        # This is a statistical property, so we test with multiple values
        assert all(isinstance(r, (int, float)) for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
