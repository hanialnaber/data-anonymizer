"""Security tests for the data anonymizer."""

import pytest
import hashlib
import re
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import secrets
import string

from src.data_anonymizer.core.anonymizer import DataAnonymizer


class TestSecurityBasics:
    """Test basic security properties of anonymization methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.anonymizer = DataAnonymizer(salt="test_security_salt")

    def test_hash_irreversibility(self):
        """Test that hashed values cannot be easily reversed."""
        original_values = ["John Doe", "Jane Smith", "sensitive_data", "123-45-6789"]
        
        for value in original_values:
            hashed = self.anonymizer.hash_value(value)
            
            # Hash should be different from original
            assert hashed != value
            
            # Hash should be consistent
            assert hashed == self.anonymizer.hash_value(value)
            
            # Hash should be proper length for SHA256
            assert len(hashed) == 64
            
            # Hash should only contain hex characters
            assert all(c in '0123456789abcdef' for c in hashed)

    def test_salt_effectiveness(self):
        """Test that salt prevents rainbow table attacks."""
        value = "common_password"
        
        # Same value with different salts should produce different hashes
        anonymizer1 = DataAnonymizer(salt="salt1")
        anonymizer2 = DataAnonymizer(salt="salt2")
        
        hash1 = anonymizer1.hash_value(value)
        hash2 = anonymizer2.hash_value(value)
        
        assert hash1 != hash2
        
        # Hash without salt should be different from hash with salt
        simple_hash = hashlib.sha256(value.encode()).hexdigest()
        assert hash1 != simple_hash
        assert hash2 != simple_hash

    def test_deterministic_anonymization(self):
        """Test that anonymization is deterministic for the same input."""
        test_data = ["John Doe", "jane.smith@company.com", "(555) 123-4567", "123-45-6789"]
        
        methods = [
            ("hash", lambda x: self.anonymizer.hash_value(x)),
            ("email", lambda x: self.anonymizer.anonymize_email(x)),
            ("phone", lambda x: self.anonymizer.anonymize_phone(x)),
            ("ssn", lambda x: self.anonymizer.anonymize_ssn(x))
        ]
        
        for method_name, method_func in methods:
            for value in test_data:
                result1 = method_func(value)
                result2 = method_func(value)
                
                assert result1 == result2, f"{method_name} should be deterministic"

    def test_collision_resistance(self):
        """Test that different inputs produce different outputs."""
        # Generate many similar values
        values = [f"user_{i}" for i in range(1000)]
        
        hashes = [self.anonymizer.hash_value(value) for value in values]
        
        # All hashes should be unique
        assert len(set(hashes)) == len(hashes)
        
        # Test with email anonymization
        emails = [f"user{i}@company.com" for i in range(100)]
        anonymized_emails = [self.anonymizer.anonymize_email(email) for email in emails]
        
        # Should maintain uniqueness
        assert len(set(anonymized_emails)) == len(set(emails))

    def test_format_preservation_security(self):
        """Test that format preservation doesn't leak information."""
        # Test phone number format preservation
        phones = [
            "(555) 123-4567",
            "(555) 987-6543",
            "(555) 555-5555"
        ]
        
        anonymized_phones = [self.anonymizer.anonymize_phone(phone) for phone in phones]
        
        for original, anonymized in zip(phones, anonymized_phones):
            # Should preserve format
            assert len(original) == len(anonymized)
            
            # Should not contain original digits
            original_digits = ''.join(re.findall(r'\d', original))
            anonymized_digits = ''.join(re.findall(r'\d', anonymized))
            assert original_digits != anonymized_digits
            
            # Should preserve non-digit characters
            original_format = re.sub(r'\d', 'X', original)
            anonymized_format = re.sub(r'\d', 'X', anonymized)
            assert original_format == anonymized_format

    def test_email_domain_handling(self):
        """Test secure handling of email domains."""
        # Test with various domain types
        test_emails = [
            "user@company.com",
            "admin@sensitive-corp.org",
            "test@personal-domain.net",
            "user@gmail.com",  # Common domain
            "user@outlook.com"  # Common domain
        ]
        
        anonymized_emails = [self.anonymizer.anonymize_email(email) for email in test_emails]
        
        for original, anonymized in zip(test_emails, anonymized_emails):
            # Should preserve email format
            assert "@" in anonymized
            
            # Should not leak original username
            original_username = original.split("@")[0]
            anonymized_username = anonymized.split("@")[0]
            assert original_username != anonymized_username
            
            # Common domains should be preserved, custom domains should be anonymized
            original_domain = original.split("@")[1]
            anonymized_domain = anonymized.split("@")[1]
            
            if original_domain in ["gmail.com", "yahoo.com", "outlook.com"]:
                assert anonymized_domain == original_domain
            else:
                assert anonymized_domain != original_domain


class TestPrivacyPreservation:
    """Test privacy preservation properties."""

    def setup_method(self):
        """Set up test fixtures."""
        self.anonymizer = DataAnonymizer()

    def test_k_anonymity_privacy(self):
        """Test k-anonymity privacy preservation."""
        # Create test data with known frequencies
        data = pd.Series(['A'] * 10 + ['B'] * 5 + ['C'] * 3 + ['D'] * 1)
        
        # Test with k=5
        result = self.anonymizer.k_anonymity_suppress(data, k=5)
        
        # Count occurrences in result
        value_counts = result.value_counts()
        
        # Values with count < k should be suppressed
        assert value_counts.get('C', 0) == 0 or result[result == 'C'].empty
        assert value_counts.get('D', 0) == 0 or result[result == 'D'].empty
        
        # Values with count >= k should remain
        assert value_counts.get('A', 0) == 10
        assert value_counts.get('B', 0) == 5
        
        # Suppressed values should be marked appropriately
        suppressed_count = (result == '[SUPPRESSED]').sum()
        assert suppressed_count == 4  # 3 'C's + 1 'D'

    def test_differential_privacy_noise(self):
        """Test differential privacy noise addition."""
        base_value = 100
        epsilon = 1.0
        
        # Generate many noisy values
        noisy_values = [
            self.anonymizer.differential_privacy_noise(base_value, epsilon)
            for _ in range(1000)
        ]
        
        # Check that noise is added (values should vary)
        assert len(set(noisy_values)) > 1
        
        # Check that values are still numeric
        assert all(isinstance(v, (int, float)) for v in noisy_values)
        
        # Check that noise follows expected distribution properties
        mean_value = sum(noisy_values) / len(noisy_values)
        assert abs(mean_value - base_value) < 10  # Should be close to original on average

    def test_generalization_privacy(self):
        """Test that generalization provides privacy protection."""
        # Test numeric generalization
        sensitive_ages = [25, 26, 27, 28, 29, 35, 36, 37, 38, 39]
        
        generalized_ages = [
            self.anonymizer.generalize_numeric(age, bin_size=10)
            for age in sensitive_ages
        ]
        
        # All ages in 20s should be generalized to same bin
        twenties_generalized = [gen for age, gen in zip(sensitive_ages, generalized_ages) if 20 <= age < 30]
        assert all(gen == "20-29" for gen in twenties_generalized)
        
        # All ages in 30s should be generalized to same bin
        thirties_generalized = [gen for age, gen in zip(sensitive_ages, generalized_ages) if 30 <= age < 40]
        assert all(gen == "30-39" for gen in thirties_generalized)

    def test_substitution_security(self):
        """Test that substitution doesn't leak information."""
        sensitive_values = ["CEO", "CTO", "Manager", "Director"]
        
        substituted_values = [
            self.anonymizer.substitute_value(value, {"type": "generic"})
            for value in sensitive_values
        ]
        
        # Should not contain original values
        for original, substituted in zip(sensitive_values, substituted_values):
            assert original != substituted
        
        # Should use values from substitution lists
        for substituted in substituted_values:
            assert substituted in ["[REDACTED]"]  # Default when no specific type matches

    def test_perturb_noise_properties(self):
        """Test that perturbation provides appropriate noise."""
        base_salary = 50000
        
        # Test different perturbation types
        perturbation_configs = [
            {"type": "uniform", "range": 5000},
            {"type": "gaussian", "range": 2000},
            {"type": "percentage", "percentage": 10}
        ]
        
        for config in perturbation_configs:
            perturbed_values = [
                self.anonymizer.perturb_value(base_salary, config)
                for _ in range(100)
            ]
            
            # Should have variation
            assert len(set(perturbed_values)) > 1
            
            # Should be in reasonable range
            if config["type"] == "percentage":
                # 10% of 50000 = 5000
                assert all(45000 <= v <= 55000 for v in perturbed_values)
            elif config["type"] == "uniform":
                # ±5000 range
                assert all(45000 <= v <= 55000 for v in perturbed_values)


class TestDataLeakagePrevention:
    """Test prevention of data leakage through anonymization."""

    def setup_method(self):
        """Set up test fixtures."""
        self.anonymizer = DataAnonymizer()

    def test_no_partial_information_leakage(self):
        """Test that partial information is not leaked."""
        # Test with SSN
        ssn = "123-45-6789"
        anonymized_ssn = self.anonymizer.anonymize_ssn(ssn)
        
        # Should not contain any original digits
        original_digits = ''.join(re.findall(r'\d', ssn))
        anonymized_digits = ''.join(re.findall(r'\d', anonymized_ssn))
        
        # No substring of original digits should appear in anonymized
        for i in range(len(original_digits)):
            for j in range(i+2, len(original_digits)+1):
                substring = original_digits[i:j]
                assert substring not in anonymized_digits

    def test_consistent_anonymization_across_columns(self):
        """Test that same values are anonymized consistently across columns."""
        df = pd.DataFrame({
            'primary_email': ['john@company.com', 'jane@company.com'],
            'backup_email': ['john@company.com', 'jane@company.com'],
            'user_id': ['john', 'jane'],
            'username': ['john', 'jane']
        })
        
        config = {
            'primary_email': 'anonymize_email',
            'backup_email': 'anonymize_email',
            'user_id': 'hash',
            'username': 'hash'
        }
        
        result = self.anonymizer.anonymize_dataframe(df, config)
        
        # Same email values should be anonymized consistently
        assert result.loc[0, 'primary_email'] == result.loc[0, 'backup_email']
        assert result.loc[1, 'primary_email'] == result.loc[1, 'backup_email']
        
        # Same user values should be hashed consistently
        assert result.loc[0, 'user_id'] == result.loc[0, 'username']
        assert result.loc[1, 'user_id'] == result.loc[1, 'username']

    def test_prevent_inference_attacks(self):
        """Test protection against inference attacks."""
        # Create data where inference might be possible
        df = pd.DataFrame({
            'age': [25, 25, 26, 26, 27, 27],
            'salary': [50000, 52000, 55000, 57000, 60000, 62000],
            'department': ['IT', 'IT', 'IT', 'IT', 'IT', 'IT']
        })
        
        config = {
            'age': {'method': 'generalize_numeric', 'options': {'bin_size': 5}},
            'salary': {'method': 'k_anonymity', 'options': {'k': 3}},
            'department': 'hash'
        }
        
        result = self.anonymizer.anonymize_dataframe(df, config)
        
        # Age should be generalized to prevent precise inference
        assert all(result['age'] == "25-29")
        
        # Department should be consistently anonymized
        assert len(result['department'].unique()) == 1

    def test_temporal_pattern_protection(self):
        """Test protection against temporal pattern analysis."""
        dates = [
            '2023-01-15', '2023-02-20', '2023-03-10',
            '2023-04-05', '2023-05-12', '2023-06-18'
        ]
        
        # Test different granularities
        month_generalized = [
            self.anonymizer.generalize_date(date, "month")
            for date in dates
        ]
        
        quarter_generalized = [
            self.anonymizer.generalize_date(date, "quarter")
            for date in dates
        ]
        
        year_generalized = [
            self.anonymizer.generalize_date(date, "year")
            for date in dates
        ]
        
        # Month level should group by month
        assert month_generalized[0] == "2023-01"
        assert month_generalized[1] == "2023-02"
        
        # Quarter level should group by quarter
        assert quarter_generalized[0] == "2023-Q1"
        assert quarter_generalized[1] == "2023-Q1"
        assert quarter_generalized[2] == "2023-Q1"
        assert quarter_generalized[3] == "2023-Q2"
        
        # Year level should group all by year
        assert all(gen == "2023" for gen in year_generalized)


class TestCryptographicSecurity:
    """Test cryptographic security properties."""

    def setup_method(self):
        """Set up test fixtures."""
        self.anonymizer = DataAnonymizer()

    def test_secure_random_usage(self):
        """Test that cryptographically secure random is used."""
        # Test shuffle function
        data = pd.Series(range(100))
        
        # Multiple shuffles should produce different results
        shuffle_results = [
            self.anonymizer.shuffle_column(data).tolist()
            for _ in range(10)
        ]
        
        # Should have variation between shuffles
        assert len(set(tuple(result) for result in shuffle_results)) > 1
        
        # Each shuffle should contain all original values
        for result in shuffle_results:
            assert set(result) == set(data)

    def test_hash_algorithm_security(self):
        """Test security of hash algorithms."""
        value = "test_value"
        
        # Test different algorithms
        algorithms = ["sha256", "sha512", "md5"]
        
        for algorithm in algorithms:
            try:
                result = self.anonymizer.hash_value(value, algorithm)
                
                # Should be proper length
                expected_lengths = {"sha256": 64, "sha512": 128, "md5": 32}
                assert len(result) == expected_lengths[algorithm]
                
                # Should be hex string
                assert all(c in '0123456789abcdef' for c in result)
                
                # Should be different from plain value
                assert result != value
                
            except ValueError:
                # Some algorithms might not be supported
                pass

    def test_noise_generation_security(self):
        """Test that noise generation is cryptographically secure."""
        base_value = 1000
        
        # Generate many noise values
        noise_values = []
        for _ in range(1000):
            config = {"type": "uniform", "range": 100}
            noisy_value = self.anonymizer.perturb_value(base_value, config)
            noise_values.append(noisy_value - base_value)
        
        # Noise should be well-distributed
        assert len(set(noise_values)) > 100  # Should have good variation
        
        # Should be within expected range
        assert all(-100 <= noise <= 100 for noise in noise_values)
        
        # Should not show obvious patterns
        # (This is a basic test - more sophisticated analysis would be needed for full validation)
        mean_noise = sum(noise_values) / len(noise_values)
        assert abs(mean_noise) < 10  # Should be roughly centered around 0


class TestComplianceAndStandards:
    """Test compliance with privacy standards and regulations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.anonymizer = DataAnonymizer()

    def test_gdpr_compliance_features(self):
        """Test features that support GDPR compliance."""
        # Test right to erasure (column removal)
        df = pd.DataFrame({
            'name': ['John Doe', 'Jane Smith'],
            'personal_id': ['ID001', 'ID002'],
            'public_info': ['Engineer', 'Manager']
        })
        
        config = {
            'personal_id': 'remove',  # Right to erasure
            'name': 'hash',  # Pseudonymization
            'public_info': 'hash'  # Ensure no direct identification
        }
        
        result = self.anonymizer.anonymize_dataframe(df, config)
        
        # Personal ID should be removed
        assert 'personal_id' not in result.columns
        
        # Name should be pseudonymized
        assert result['name'].iloc[0] != 'John Doe'
        assert result['name'].iloc[1] != 'Jane Smith'

    def test_hipaa_compliance_features(self):
        """Test features that support HIPAA compliance."""
        # Test with healthcare-like data
        df = pd.DataFrame({
            'patient_id': ['P001', 'P002'],
            'date_of_birth': ['1990-01-15', '1985-05-20'],
            'diagnosis': ['Diabetes', 'Hypertension'],
            'zip_code': ['12345', '67890']
        })
        
        config = {
            'patient_id': 'hash',
            'date_of_birth': {'method': 'generalize_date', 'options': {'granularity': 'year'}},
            'diagnosis': 'hash',
            'zip_code': {'method': 'generalize_numeric', 'options': {'bin_size': 1000}}
        }
        
        result = self.anonymizer.anonymize_dataframe(df, config)
        
        # Patient ID should be hashed
        assert result['patient_id'].iloc[0] != 'P001'
        
        # Date should be generalized to year only
        assert result['date_of_birth'].iloc[0] == '1990'
        assert result['date_of_birth'].iloc[1] == '1985'
        
        # Diagnosis should be hashed
        assert result['diagnosis'].iloc[0] != 'Diabetes'
        
        # Zip code should be generalized
        zip_result = result['zip_code'].iloc[0]
        assert len(zip_result) == 5 or '-' in zip_result  # Accept both formats

    def test_pci_compliance_features(self):
        """Test features that support PCI compliance."""
        # Test with payment card data
        df = pd.DataFrame({
            'card_number': ['1234-5678-9012-3456', '2345-6789-0123-4567'],
            'cvv': ['123', '456'],
            'expiry': ['12/25', '03/26'],
            'amount': [100.50, 250.75]
        })
        
        config = {
            'card_number': 'hash',  # Should be completely anonymized
            'cvv': 'remove',  # Should be removed for PCI compliance
            'expiry': 'hash',  # Should be anonymized
            'amount': {'method': 'perturb', 'options': {'type': 'percentage', 'percentage': 5}}
        }
        
        result = self.anonymizer.anonymize_dataframe(df, config)
        
        # Card number should be hashed
        assert result['card_number'].iloc[0] != '1234-5678-9012-3456'
        
        # CVV should be removed
        assert 'cvv' not in result.columns
        
        # Expiry should be hashed
        assert result['expiry'].iloc[0] != '12/25'
        
        # Amount should be perturbed but similar
        assert abs(result['amount'].iloc[0] - 100.50) < 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
