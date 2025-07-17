"""Core anonymization functionality."""

import hashlib
import json
import os
import random
import re
import secrets
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from email_validator import EmailNotValidError, validate_email

from .config import Config


class DataAnonymizer:
    """Data anonymization with multiple techniques."""

    def __init__(self, salt: Optional[str] = None):
        """Initialize the anonymizer with optional salt."""
        self.salt = salt or "default_salt"
        self.config = Config()
        # Use cryptographically secure random for all operations
        self.secure_random = secrets.SystemRandom()

        # Common substitution lists for different data types
        self.substitution_lists = {
            "names": [
                "John Doe",
                "Jane Smith",
                "Robert Johnson",
                "Emily Davis",
                "Michael Brown",
                "Sarah Wilson",
                "David Miller",
                "Lisa Garcia",
                "Chris Martinez",
                "Anna Taylor",
            ],
            "companies": [
                "Acme Corp",
                "Beta Inc",
                "Gamma LLC",
                "Delta Ltd",
                "Alpha Systems",
                "Omega Solutions",
                "Phoenix Group",
                "Titan Industries",
                "Nova Corp",
                "Prime Tech",
            ],
            "cities": [
                "Springfield",
                "Franklin",
                "Georgetown",
                "Madison",
                "Riverside",
                "Arlington",
                "Fairview",
                "Greenville",
                "Oakland",
                "Clayton",
            ],
            "domains": [
                "example.com",
                "testdomain.org",
                "sample.net",
                "placeholder.co",
                "anonymous.info",
                "generic.com",
                "standard.org",
                "default.net",
            ],
            "countries": [
                "Country A",
                "Country B",
                "Country C",
                "Country D",
                "Country E",
            ],
        }

    def _generate_secure_hash(self, value: Any, algorithm: str = "sha256") -> str:
        """Generate secure hash with salt using specified algorithm."""
        # Convert value to string and add salt
        input_str = f"{value}{self.salt}"

        # Use specified hash algorithm
        if algorithm == "sha256":
            return hashlib.sha256(input_str.encode()).hexdigest()
        elif algorithm == "sha512":
            return hashlib.sha512(input_str.encode()).hexdigest()
        elif algorithm == "md5":
            # MD5 for backward compatibility (not recommended for sensitive data)
            return hashlib.md5(input_str.encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    def hash_value(self, value: Any, algorithm: str = "sha256") -> str:
        """Hash a value with salt using specified algorithm."""
        return self._generate_secure_hash(value, algorithm)

    def mask_value(
        self, value: Any, mask_char: str = "*", preserve_length: bool = True
    ) -> str:
        """Mask a value by replacing characters with mask character."""
        str_value = str(value)
        if preserve_length:
            return mask_char * len(str_value)
        else:
            # Show first and last character for readability
            if len(str_value) <= 2:
                return mask_char * len(str_value)
            return str_value[0] + mask_char * (len(str_value) - 2) + str_value[-1]

    def pseudonymize_value(self, value: Any, prefix: str = "ID") -> str:
        """Replace value with a pseudonym (deterministic replacement)."""
        # Generate deterministic pseudonym based on hash
        hash_val = self._generate_secure_hash(value, "sha256")
        # Use first 8 characters of hash to create pseudonym
        return f"{prefix}_{hash_val[:8]}"

    def generalize_numeric(self, value: Any, bin_size: int = 10) -> str:
        """Generalize numeric values into ranges."""
        if not isinstance(value, (int, float)):
            return str(value)

        # Convert to int for binning
        num_value = int(value)
        bin_start = (num_value // bin_size) * bin_size
        bin_end = bin_start + bin_size - 1
        return f"{bin_start}-{bin_end}"

    def generalize_date(self, value: Any, granularity: str = "month") -> str:
        """Generalize dates to reduce precision."""
        if isinstance(value, str):
            try:
                # Try to parse common date formats
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        date_obj = datetime.strptime(value, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return str(value)  # Return original if can't parse
            except:
                return str(value)
        elif isinstance(value, datetime):
            date_obj = value
        else:
            return str(value)

        # Apply generalization
        if granularity == "year":
            return str(date_obj.year)
        elif granularity == "month":
            return f"{date_obj.year}-{date_obj.month:02d}"
        elif granularity == "quarter":
            quarter = (date_obj.month - 1) // 3 + 1
            return f"{date_obj.year}-Q{quarter}"
        else:
            return str(value)

    def anonymize_email(self, email: str) -> str:
        """Anonymize email addresses while preserving domain structure."""
        if not isinstance(email, str) or "@" not in email:
            return str(email)

        try:
            # Split email into local and domain parts
            local, domain = email.split("@", 1)

            # Generate anonymous local part
            hash_local = self._generate_secure_hash(local, "sha256")
            anon_local = f"user{hash_local[:8]}"

            # Optionally anonymize domain
            if domain not in [
                "gmail.com",
                "yahoo.com",
                "outlook.com",
            ]:  # Keep common domains
                domain_parts = domain.split(".")
                if len(domain_parts) >= 2:
                    # Keep TLD, anonymize the rest
                    tld = domain_parts[-1]
                    hash_domain = self._generate_secure_hash(domain, "sha256")
                    anon_domain = f"company{hash_domain[:6]}.{tld}"
                    domain = anon_domain

            return f"{anon_local}@{domain}"
        except:
            return "anonymous@example.com"

    def anonymize_phone(self, phone: str) -> str:
        """Anonymize phone numbers while preserving format."""
        if not isinstance(phone, str):
            return str(phone)

        # Extract digits only
        digits = re.sub(r"\D", "", phone)

        if len(digits) >= 7:
            # Generate consistent fake phone number
            hash_val = self._generate_secure_hash(phone, "sha256")
            fake_digits = "".join(
                [
                    str(int(hash_val[i : i + 2], 16) % 10)
                    for i in range(0, len(digits) * 2, 2)
                ]
            )[: len(digits)]

            # Preserve original format
            result = phone
            digit_index = 0
            for i, char in enumerate(phone):
                if char.isdigit() and digit_index < len(fake_digits):
                    result = result[:i] + fake_digits[digit_index] + result[i + 1 :]
                    digit_index += 1

            return result
        else:
            return phone

    def anonymize_ssn(self, ssn: str) -> str:
        """Anonymize Social Security Numbers."""
        if not isinstance(ssn, str):
            return str(ssn)

        # Generate consistent fake SSN using numeric values
        hash_val = self._generate_secure_hash(ssn, "sha256")
        # Convert hash to numeric values only
        numeric_hash = ''.join(str(ord(c) % 10) for c in hash_val)
        fake_ssn = f"{numeric_hash[:3]}-{numeric_hash[3:5]}-{numeric_hash[5:9]}"

        # Preserve original format if different
        if re.match(r"\d{3}-\d{2}-\d{4}", ssn):
            return fake_ssn
        elif re.match(r"\d{9}", ssn):
            return fake_ssn.replace("-", "")
        else:
            return fake_ssn

    def k_anonymity_suppress(self, series: pd.Series, k: int = 5) -> pd.Series:
        """Suppress values that appear less than k times."""
        value_counts = series.value_counts()
        suppressed = series.copy()

        for value, count in value_counts.items():
            if count < k:
                suppressed = suppressed.replace(value, "[SUPPRESSED]")

        return suppressed

    def differential_privacy_noise(
        self, value: Any, epsilon: float = 1.0
    ) -> Union[int, float, Any]:
        """Add Laplace noise for differential privacy."""
        if not isinstance(value, (int, float)):
            return value

        # Calculate sensitivity (assuming it's 1 for most cases)
        sensitivity = 1.0
        scale = sensitivity / epsilon

        # Add Laplace noise
        noise = self.secure_random.gauss(0, scale)

        if isinstance(value, int):
            return int(value + noise)
        else:
            return value + noise

    def substitute_value(self, value: Any, logic_details: Dict[str, Any]) -> str:
        """Enhanced substitution with context-aware replacements."""
        replacement_list = logic_details.get("list", None)
        data_type = logic_details.get("type", "generic")

        if replacement_list:
            return self.secure_random.choice(replacement_list)
        elif data_type in self.substitution_lists:
            return self.secure_random.choice(self.substitution_lists[data_type])
        else:
            return "[REDACTED]"

    def shuffle_column(self, series: pd.Series) -> pd.Series:
        """Shuffle values in a pandas Series using cryptographically secure random."""
        shuffled = series.copy()
        # Convert to list for shuffling
        values = shuffled.tolist()
        self.secure_random.shuffle(values)
        return pd.Series(values, index=series.index)

    def perturb_value(
        self, value: Any, logic_details: Dict[str, Any]
    ) -> Union[int, float, Any]:
        """Add noise to numerical values with enhanced options."""
        if not isinstance(value, (int, float)):
            return value

        perturbation_type = logic_details.get("type", "uniform")
        perturbation_range = logic_details.get(
            "range", abs(value) * 0.1
        )  # 10% of value by default

        if perturbation_type == "uniform":
            noise = self.secure_random.uniform(-perturbation_range, perturbation_range)
        elif perturbation_type == "gaussian":
            noise = self.secure_random.gauss(0, perturbation_range)
        elif perturbation_type == "percentage":
            percentage = logic_details.get("percentage", 10)  # 10% by default
            noise = (
                self.secure_random.uniform(-percentage / 100, percentage / 100) * value
            )
        else:
            noise = self.secure_random.uniform(-perturbation_range, perturbation_range)

        result = value + noise

        # Ensure non-negative for certain types
        if logic_details.get("non_negative", False) and result < 0:
            result = abs(result)

        if isinstance(value, int):
            return int(result)
        else:
            return result

    def anonymize_dataframe(
        self, df: pd.DataFrame, masking_config: Dict[str, Any]
    ) -> pd.DataFrame:
        """Anonymize a single DataFrame based on enhanced masking configuration."""
        df_anon = df.copy()

        for col, config in masking_config.items():
            if col not in df_anon.columns:
                continue

            # Handle both simple string method and complex dictionary config
            if isinstance(config, str):
                method = config
                options = {}
            else:
                method = config.get("method", "hash")
                options = config.get("options", {})

            try:
                if method == "hash":
                    algorithm = options.get("algorithm", "sha256")
                    df_anon[col] = (
                        df_anon[col]
                        .astype(str)
                        .apply(lambda x: self.hash_value(x, algorithm))
                    )

                elif method == "mask":
                    mask_char = options.get("mask_char", "*")
                    preserve_length = options.get("preserve_length", True)
                    df_anon[col] = df_anon[col].apply(
                        lambda x: self.mask_value(x, mask_char, preserve_length)
                    )

                elif method == "pseudonymize":
                    prefix = options.get("prefix", "ID")
                    df_anon[col] = df_anon[col].apply(
                        lambda x: self.pseudonymize_value(x, prefix)
                    )

                elif method == "generalize_numeric":
                    bin_size = options.get("bin_size", 10)
                    df_anon[col] = df_anon[col].apply(
                        lambda x: self.generalize_numeric(x, bin_size)
                    )

                elif method == "generalize_date":
                    granularity = options.get("granularity", "month")
                    df_anon[col] = df_anon[col].apply(
                        lambda x: self.generalize_date(x, granularity)
                    )

                elif method == "anonymize_email":
                    df_anon[col] = df_anon[col].apply(self.anonymize_email)

                elif method == "anonymize_phone":
                    df_anon[col] = df_anon[col].apply(self.anonymize_phone)

                elif method == "anonymize_ssn":
                    df_anon[col] = df_anon[col].apply(self.anonymize_ssn)

                elif method == "k_anonymity":
                    k = options.get("k", 5)
                    df_anon[col] = self.k_anonymity_suppress(df_anon[col], k)

                elif method == "differential_privacy":
                    epsilon = options.get("epsilon", 1.0)
                    df_anon[col] = df_anon[col].apply(
                        lambda x: self.differential_privacy_noise(x, epsilon)
                    )

                elif method == "shuffle":
                    df_anon[col] = self.shuffle_column(df_anon[col])

                elif method == "substitute":
                    df_anon[col] = df_anon[col].apply(
                        lambda x: self.substitute_value(x, options)
                    )

                elif method == "perturb":
                    df_anon[col] = df_anon[col].apply(
                        lambda x: self.perturb_value(x, options)
                    )

                elif method == "remove":
                    # Complete removal of the column
                    df_anon = df_anon.drop(columns=[col])

                else:
                    # Default to hashing for unknown methods
                    df_anon[col] = (
                        df_anon[col].astype(str).apply(lambda x: self.hash_value(x))
                    )

            except Exception as e:
                # Log error and skip problematic column
                print(f"Error processing column {col} with method {method}: {e}")
                continue

        return df_anon

    def load_data(
        self, input_path: str, selected_sheet: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """Load data from CSV or Excel file."""
        input_path = Path(input_path)

        if input_path.suffix.lower() == ".csv":
            df = pd.read_csv(input_path)
            return {"Sheet1": df}
        elif input_path.suffix.lower() in [".xlsx", ".xls"]:
            xls = pd.ExcelFile(input_path)
            if selected_sheet and selected_sheet in xls.sheet_names:
                return {selected_sheet: xls.parse(selected_sheet)}
            else:
                return {sheet: xls.parse(sheet) for sheet in xls.sheet_names}
        else:
            raise ValueError(f"Unsupported file type: {input_path.suffix}")

    def save_data(self, data: Dict[str, pd.DataFrame], output_path: str) -> None:
        """Save anonymized data to file."""
        output_path = Path(output_path)

        if output_path.suffix.lower() == ".csv":
            # For CSV, save the first sheet only
            first_sheet = next(iter(data.values()))
            first_sheet.to_csv(output_path, index=False)
        elif output_path.suffix.lower() in [".xlsx", ".xls"]:
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                for sheet_name, df in data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            raise ValueError(f"Unsupported output format: {output_path.suffix}")


def run_anonymization_job(
    input_path: str,
    output_path: str,
    output_format: str,
    masking_config: Union[str, Dict[str, Any]],
    selected_sheet: Optional[str] = None,
) -> None:
    """Run the anonymization job (backward compatibility function)."""
    # Parse configs if they are strings
    if isinstance(masking_config, str):
        masking_config = json.loads(masking_config)

    # Initialize anonymizer
    anonymizer = DataAnonymizer()

    # Load data
    sheets = anonymizer.load_data(input_path, selected_sheet)

    # Anonymize data
    anonymized_sheets = {}
    for sheet_name, df in sheets.items():
        sheet_masking_config = masking_config.get(sheet_name, {})
        anonymized_sheets[sheet_name] = anonymizer.anonymize_dataframe(
            df, sheet_masking_config
        )

    # Save anonymized data
    anonymizer.save_data(anonymized_sheets, output_path)
