"""Performance tests for the data anonymizer."""

import pytest
import time
import psutil
import os
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
from memory_profiler import profile
import threading
import concurrent.futures

from src.data_anonymizer.core.anonymizer import DataAnonymizer


class TestPerformanceBasics:
    """Basic performance tests for anonymization methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.anonymizer = DataAnonymizer()

    def test_hash_performance(self):
        """Test hashing performance with different data sizes."""
        sizes = [100, 1000, 10000]
        
        for size in sizes:
            data = [f"test_value_{i}" for i in range(size)]
            
            start_time = time.time()
            results = [self.anonymizer.hash_value(value) for value in data]
            end_time = time.time()
            
            processing_time = end_time - start_time
            throughput = size / processing_time
            
            print(f"Hash performance for {size} items: {processing_time:.4f}s, {throughput:.2f} items/sec")
            
            # Basic performance assertions
            assert processing_time < 10  # Should complete within 10 seconds
            assert len(results) == size
            assert all(len(r) == 64 for r in results)  # SHA256 length

    def test_email_anonymization_performance(self):
        """Test email anonymization performance."""
        sizes = [100, 1000, 5000]
        
        for size in sizes:
            emails = [f"user{i}@company{i%10}.com" for i in range(size)]
            
            start_time = time.time()
            results = [self.anonymizer.anonymize_email(email) for email in emails]
            end_time = time.time()
            
            processing_time = end_time - start_time
            throughput = size / processing_time
            
            print(f"Email anonymization for {size} items: {processing_time:.4f}s, {throughput:.2f} items/sec")
            
            assert processing_time < 15
            assert len(results) == size
            assert all("@" in email for email in results)

    def test_phone_anonymization_performance(self):
        """Test phone anonymization performance."""
        sizes = [100, 1000, 5000]
        
        for size in sizes:
            phones = [f"({200 + i%800}) {200 + i%800}-{1000 + i%9000}" for i in range(size)]
            
            start_time = time.time()
            results = [self.anonymizer.anonymize_phone(phone) for phone in phones]
            end_time = time.time()
            
            processing_time = end_time - start_time
            throughput = size / processing_time
            
            print(f"Phone anonymization for {size} items: {processing_time:.4f}s, {throughput:.2f} items/sec")
            
            assert processing_time < 15
            assert len(results) == size


class TestLargeDatasetPerformance:
    """Test performance with large datasets."""

    def setup_method(self):
        """Set up test fixtures."""
        self.anonymizer = DataAnonymizer()

    def create_large_dataset(self, rows=100000):
        """Create a large dataset for performance testing."""
        np.random.seed(42)  # For reproducibility
        
        names = [f"Person_{i}" for i in range(rows)]
        emails = [f"user{i}@company{i%100}.com" for i in range(rows)]
        phones = [f"({200 + i%800}) {200 + i%800}-{1000 + i%9000}" for i in range(rows)]
        ages = np.random.randint(18, 80, rows)
        salaries = np.random.randint(30000, 150000, rows)
        
        return pd.DataFrame({
            'name': names,
            'email': emails,
            'phone': phones,
            'age': ages,
            'salary': salaries,
            'department': np.random.choice(['IT', 'HR', 'Finance', 'Marketing', 'Sales'], rows)
        })

    def test_large_dataset_anonymization(self):
        """Test anonymization performance with large datasets."""
        dataset_sizes = [10000, 50000, 100000]
        
        for size in dataset_sizes:
            df = self.create_large_dataset(size)
            
            config = {
                'name': 'hash',
                'email': 'anonymize_email',
                'phone': 'anonymize_phone',
                'age': {'method': 'generalize_numeric', 'options': {'bin_size': 10}},
                'salary': {'method': 'perturb', 'options': {'type': 'percentage', 'percentage': 10}}
            }
            
            # Monitor memory usage
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            start_time = time.time()
            result = self.anonymizer.anonymize_dataframe(df, config)
            end_time = time.time()
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = memory_after - memory_before
            
            processing_time = end_time - start_time
            throughput = size / processing_time
            
            print(f"Large dataset ({size} rows): {processing_time:.4f}s, {throughput:.2f} rows/sec, Memory: {memory_used:.2f}MB")
            
            # Performance assertions
            assert processing_time < 60  # Should complete within 1 minute
            assert len(result) == size
            assert memory_used < 1000  # Should use less than 1GB additional memory

    def test_chunked_processing_performance(self):
        """Test performance with chunked processing for very large datasets."""
        large_df = self.create_large_dataset(100000)
        
        config = {
            'name': 'hash',
            'email': 'anonymize_email',
            'age': {'method': 'generalize_numeric', 'options': {'bin_size': 10}}
        }
        
        chunk_sizes = [1000, 5000, 10000]
        
        for chunk_size in chunk_sizes:
            chunks = [large_df[i:i+chunk_size] for i in range(0, len(large_df), chunk_size)]
            
            start_time = time.time()
            anonymized_chunks = []
            
            for chunk in chunks:
                anonymized_chunk = self.anonymizer.anonymize_dataframe(chunk, config)
                anonymized_chunks.append(anonymized_chunk)
            
            result = pd.concat(anonymized_chunks, ignore_index=True)
            end_time = time.time()
            
            processing_time = end_time - start_time
            throughput = len(large_df) / processing_time
            
            print(f"Chunked processing (chunk size {chunk_size}): {processing_time:.4f}s, {throughput:.2f} rows/sec")
            
            assert len(result) == len(large_df)
            assert processing_time < 120  # Should complete within 2 minutes

    def test_concurrent_anonymization_performance(self):
        """Test concurrent anonymization performance."""
        df = self.create_large_dataset(50000)
        
        config = {
            'name': 'hash',
            'email': 'anonymize_email',
            'phone': 'anonymize_phone'
        }
        
        # Split data into chunks for concurrent processing
        num_workers = 4
        chunk_size = len(df) // num_workers
        chunks = [df[i*chunk_size:(i+1)*chunk_size] for i in range(num_workers)]
        
        # Sequential processing
        start_time = time.time()
        sequential_results = []
        for chunk in chunks:
            result = self.anonymizer.anonymize_dataframe(chunk, config)
            sequential_results.append(result)
        sequential_time = time.time() - start_time
        
        # Concurrent processing
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(self.anonymizer.anonymize_dataframe, chunk, config) for chunk in chunks]
            concurrent_results = [future.result() for future in futures]
        concurrent_time = time.time() - start_time
        
        speedup = sequential_time / concurrent_time
        
        print(f"Sequential: {sequential_time:.4f}s, Concurrent: {concurrent_time:.4f}s, Speedup: {speedup:.2f}x")
        
        # Verify results are the same
        sequential_combined = pd.concat(sequential_results, ignore_index=True)
        concurrent_combined = pd.concat(concurrent_results, ignore_index=True)
        
        assert len(sequential_combined) == len(concurrent_combined)
        assert speedup > 1.0  # Should be faster with concurrency


class TestMemoryEfficiency:
    """Test memory efficiency of anonymization methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.anonymizer = DataAnonymizer()

    def test_memory_usage_scaling(self):
        """Test how memory usage scales with data size."""
        sizes = [1000, 10000, 50000]
        memory_usage = []
        
        for size in sizes:
            df = pd.DataFrame({
                'data': [f'test_value_{i}' for i in range(size)]
            })
            
            config = {'data': 'hash'}
            
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            result = self.anonymizer.anonymize_dataframe(df, config)
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = memory_after - memory_before
            
            memory_usage.append(memory_used)
            
            print(f"Size {size}: Memory used {memory_used:.2f}MB")
            
            # Clean up
            del result
            del df
        
        # Memory usage should scale reasonably (not exponentially)
        for i in range(1, len(memory_usage)):
            ratio = memory_usage[i] / memory_usage[i-1]
            assert ratio < 10  # Should not increase by more than 10x

    def test_memory_cleanup(self):
        """Test that memory is properly cleaned up after processing."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process large dataset
        df = pd.DataFrame({
            'data': [f'test_value_{i}' for i in range(100000)]
        })
        
        config = {'data': 'hash'}
        result = self.anonymizer.anonymize_dataframe(df, config)
        
        # Check memory during processing
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Clean up
        del result
        del df
        
        # Force garbage collection
        import gc
        gc.collect()
        
        # Check memory after cleanup
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"Initial: {initial_memory:.2f}MB, Peak: {peak_memory:.2f}MB, Final: {final_memory:.2f}MB")
        
        # Memory should return close to initial levels
        memory_increase = final_memory - initial_memory
        assert memory_increase < 100  # Should not have significant permanent increase


class TestFileIOPerformance:
    """Test file I/O performance for different formats."""

    def setup_method(self):
        """Set up test fixtures."""
        self.anonymizer = DataAnonymizer()

    def test_csv_io_performance(self):
        """Test CSV file I/O performance."""
        sizes = [1000, 10000, 50000]
        
        for size in sizes:
            df = pd.DataFrame({
                'name': [f'Person_{i}' for i in range(size)],
                'email': [f'user{i}@company.com' for i in range(size)],
                'age': np.random.randint(18, 80, size)
            })
            
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
                temp_path = Path(f.name)
            
            try:
                # Test write performance
                start_time = time.time()
                df.to_csv(temp_path, index=False)
                write_time = time.time() - start_time
                
                # Test read performance
                start_time = time.time()
                loaded_data = self.anonymizer.load_data(str(temp_path))
                read_time = time.time() - start_time
                
                print(f"CSV {size} rows - Write: {write_time:.4f}s, Read: {read_time:.4f}s")
                
                assert write_time < 10
                assert read_time < 10
                assert len(loaded_data['Sheet1']) == size
                
            finally:
                temp_path.unlink()

    def test_excel_io_performance(self):
        """Test Excel file I/O performance."""
        sizes = [1000, 5000, 10000]  # Smaller sizes for Excel due to overhead
        
        for size in sizes:
            df = pd.DataFrame({
                'name': [f'Person_{i}' for i in range(size)],
                'email': [f'user{i}@company.com' for i in range(size)],
                'age': np.random.randint(18, 80, size)
            })
            
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
                temp_path = Path(f.name)
            
            try:
                # Test write performance
                start_time = time.time()
                df.to_excel(temp_path, index=False)
                write_time = time.time() - start_time
                
                # Test read performance
                start_time = time.time()
                loaded_data = self.anonymizer.load_data(str(temp_path))
                read_time = time.time() - start_time
                
                print(f"Excel {size} rows - Write: {write_time:.4f}s, Read: {read_time:.4f}s")
                
                assert write_time < 30  # Excel is slower
                assert read_time < 30
                assert len(loaded_data['Sheet1']) == size
                
            finally:
                temp_path.unlink()

    def test_multisheet_excel_performance(self):
        """Test multi-sheet Excel performance."""
        sheet_sizes = [1000, 2000, 3000]
        
        sheets_data = {}
        for i, size in enumerate(sheet_sizes):
            sheets_data[f'Sheet{i+1}'] = pd.DataFrame({
                'id': range(size),
                'data': [f'value_{j}' for j in range(size)]
            })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            # Test write performance
            start_time = time.time()
            with pd.ExcelWriter(temp_path) as writer:
                for sheet_name, df in sheets_data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            write_time = time.time() - start_time
            
            # Test read performance
            start_time = time.time()
            loaded_data = self.anonymizer.load_data(str(temp_path))
            read_time = time.time() - start_time
            
            total_rows = sum(sheet_sizes)
            print(f"Multi-sheet Excel {total_rows} total rows - Write: {write_time:.4f}s, Read: {read_time:.4f}s")
            
            assert write_time < 60
            assert read_time < 60
            assert len(loaded_data) == len(sheets_data)
            
        finally:
            temp_path.unlink()


class TestMethodSpecificPerformance:
    """Test performance of specific anonymization methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.anonymizer = DataAnonymizer()

    def test_differential_privacy_performance(self):
        """Test differential privacy performance with different epsilon values."""
        data = np.random.randint(1, 1000, 10000)
        epsilon_values = [0.1, 0.5, 1.0, 2.0]
        
        for epsilon in epsilon_values:
            start_time = time.time()
            results = [self.anonymizer.differential_privacy_noise(value, epsilon) for value in data]
            end_time = time.time()
            
            processing_time = end_time - start_time
            throughput = len(data) / processing_time
            
            print(f"Differential privacy (ε={epsilon}): {processing_time:.4f}s, {throughput:.2f} items/sec")
            
            assert processing_time < 5
            assert len(results) == len(data)

    def test_k_anonymity_performance(self):
        """Test k-anonymity performance with different k values."""
        data = pd.Series(np.random.choice(['A', 'B', 'C', 'D', 'E'], 10000))
        k_values = [2, 5, 10, 20]
        
        for k in k_values:
            start_time = time.time()
            result = self.anonymizer.k_anonymity_suppress(data, k)
            end_time = time.time()
            
            processing_time = end_time - start_time
            throughput = len(data) / processing_time
            
            print(f"K-anonymity (k={k}): {processing_time:.4f}s, {throughput:.2f} items/sec")
            
            assert processing_time < 5
            assert len(result) == len(data)

    def test_generalization_performance(self):
        """Test generalization performance."""
        # Numeric generalization
        numeric_data = np.random.randint(1, 1000, 10000)
        
        start_time = time.time()
        results = [self.anonymizer.generalize_numeric(value) for value in numeric_data]
        end_time = time.time()
        
        processing_time = end_time - start_time
        throughput = len(numeric_data) / processing_time
        
        print(f"Numeric generalization: {processing_time:.4f}s, {throughput:.2f} items/sec")
        
        assert processing_time < 5
        assert len(results) == len(numeric_data)
        
        # Date generalization
        date_data = ['2023-01-01', '2023-06-15', '2023-12-31'] * 1000
        
        start_time = time.time()
        results = [self.anonymizer.generalize_date(date) for date in date_data]
        end_time = time.time()
        
        processing_time = end_time - start_time
        throughput = len(date_data) / processing_time
        
        print(f"Date generalization: {processing_time:.4f}s, {throughput:.2f} items/sec")
        
        assert processing_time < 5
        assert len(results) == len(date_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to see print statements
