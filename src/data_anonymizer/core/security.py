"""Security utilities for enhanced data privacy and protection."""

import hashlib
import os
import re
import secrets
import string
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class SecurityManager:
    """Manages security features for data anonymization."""

    def __init__(self):
        """Initialize security manager."""
        self.secure_random = secrets.SystemRandom()
        self.temp_files = {}  # Track temporary files for cleanup

    def generate_secure_salt(self, length: int = 32) -> str:
        """Generate a cryptographically secure salt."""
        alphabet = string.ascii_letters + string.digits
        return "".join(self.secure_random.choice(alphabet) for _ in range(length))

    def validate_file_security(
        self, file_path: str, max_size_mb: int = 100
    ) -> Dict[str, Any]:
        """Validate file security aspects."""
        file_path = Path(file_path)

        validation_result = {"valid": True, "issues": [], "warnings": [], "size_mb": 0}

        # Check file exists
        if not file_path.exists():
            validation_result["valid"] = False
            validation_result["issues"].append("File does not exist")
            return validation_result

        # Check file size
        file_size = file_path.stat().st_size
        size_mb = file_size / (1024 * 1024)
        validation_result["size_mb"] = size_mb

        if size_mb > max_size_mb:
            validation_result["valid"] = False
            validation_result["issues"].append(
                f"File size ({size_mb:.1f}MB) exceeds limit ({max_size_mb}MB)"
            )

        # Check file extension
        allowed_extensions = [".csv", ".xlsx", ".xls"]
        if file_path.suffix.lower() not in allowed_extensions:
            validation_result["valid"] = False
            validation_result["issues"].append(
                f"File type {file_path.suffix} not allowed"
            )

        # Check for potentially dangerous content in filename
        dangerous_patterns = ["..", "\\", "/", "<", ">", ":", '"', "|", "?", "*"]
        for pattern in dangerous_patterns:
            if pattern in file_path.name:
                validation_result["warnings"].append(
                    f"Potentially unsafe character in filename: {pattern}"
                )

        return validation_result

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal attacks."""
        # Remove path separators and other dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)
        sanitized = re.sub(r"\.\.+", ".", sanitized)  # Remove multiple dots
        sanitized = sanitized.strip(". ")  # Remove leading/trailing dots and spaces

        # Ensure filename isn't too long
        if len(sanitized) > 100:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[: 100 - len(ext)] + ext

        return sanitized

    def detect_sensitive_data_patterns(self, text: str) -> List[str]:
        """Detect potential sensitive data patterns in text."""
        patterns = {
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "phone": r"\b\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
            "date": r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
            "potential_id": r"\b[A-Z]\d{8,12}\b",
        }

        detected = []
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                detected.append(pattern_name)

        return detected

    def generate_audit_log(
        self, action: str, details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate audit log entry for anonymization operations."""
        return {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
            "session_id": self.generate_session_id(),
            "hash": self.generate_operation_hash(action, details),
        }

    def generate_session_id(self) -> str:
        """Generate unique session ID."""
        return secrets.token_hex(16)

    def generate_operation_hash(self, action: str, details: Dict[str, Any]) -> str:
        """Generate hash for operation verification."""
        content = f"{action}{str(details)}{time.time()}"
        return hashlib.sha256(content.encode()).hexdigest()

    def cleanup_temp_files(self, max_age_hours: int = 24) -> List[str]:
        """Clean up temporary files older than specified age."""
        cleaned_files = []
        current_time = datetime.now()

        for file_path, creation_time in self.temp_files.items():
            file_age = current_time - creation_time
            if file_age > timedelta(hours=max_age_hours):
                try:
                    if Path(file_path).exists():
                        Path(file_path).unlink()
                        cleaned_files.append(file_path)
                        del self.temp_files[file_path]
                except Exception as e:
                    print(f"Error cleaning up {file_path}: {e}")

        return cleaned_files

    def register_temp_file(self, file_path: str) -> None:
        """Register a temporary file for cleanup."""
        self.temp_files[file_path] = datetime.now()

    def verify_anonymization_quality(
        self, original_data: str, anonymized_data: str
    ) -> Dict[str, Any]:
        """Verify the quality of anonymization."""
        quality_report = {
            "information_loss": 0.0,
            "privacy_score": 0.0,
            "potential_issues": [],
            "recommendations": [],
        }

        # Check for obvious data leakage
        original_words = set(original_data.lower().split())
        anonymized_words = set(anonymized_data.lower().split())

        # Calculate information loss (simplified)
        common_words = original_words.intersection(anonymized_words)
        if original_words:
            quality_report["information_loss"] = len(common_words) / len(original_words)

        # Check for sensitive patterns in anonymized data
        sensitive_patterns = self.detect_sensitive_data_patterns(anonymized_data)
        if sensitive_patterns:
            quality_report["potential_issues"].extend(sensitive_patterns)
            quality_report["recommendations"].append(
                "Consider stronger anonymization for detected patterns"
            )

        # Calculate privacy score (simplified)
        privacy_score = 1.0 - quality_report["information_loss"]
        if sensitive_patterns:
            privacy_score *= 0.8  # Reduce score if sensitive patterns detected

        quality_report["privacy_score"] = privacy_score

        return quality_report


class DataValidator:
    """Validates data integrity and security."""

    @staticmethod
    def validate_column_types(data: List[str], expected_type: str) -> bool:
        """Validate that column data matches expected type."""
        if expected_type == "email":
            return all("@" in item and "." in item for item in data if item)
        elif expected_type == "phone":
            return all(re.match(r"[\d\s\-\(\)\.]+", item) for item in data if item)
        elif expected_type == "ssn":
            return all(re.match(r"\d{3}-\d{2}-\d{4}", item) for item in data if item)
        elif expected_type == "numeric":
            return all(
                str(item).replace(".", "").replace("-", "").isdigit()
                for item in data
                if item
            )
        return True

    @staticmethod
    def check_data_consistency(original_count: int, anonymized_count: int) -> bool:
        """Check if anonymized data has same number of records."""
        return original_count == anonymized_count

    @staticmethod
    def validate_anonymization_config(config: Dict[str, Any]) -> List[str]:
        """Validate anonymization configuration."""
        issues = []

        valid_methods = [
            "hash",
            "mask",
            "pseudonymize",
            "substitute",
            "shuffle",
            "perturb",
            "generalize_numeric",
            "generalize_date",
            "anonymize_email",
            "anonymize_phone",
            "anonymize_ssn",
            "k_anonymity",
            "differential_privacy",
            "remove",
        ]

        for column, method in config.items():
            if isinstance(method, dict):
                method_name = method.get("method", "")
            else:
                method_name = method

            if method_name not in valid_methods:
                issues.append(
                    f"Unknown anonymization method '{method_name}' for column '{column}'"
                )

        return issues


# Global security manager instance
security_manager = SecurityManager()
