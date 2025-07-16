"""Sample data generator utilities."""

import os
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from ..core.config import Config


class SampleDataGenerator:
    """Generate sample data for testing anonymization."""

    def __init__(self, output_dir: Optional[str] = None):
        """Initialize the generator with output directory."""
        self.config = Config()
        self.output_dir = Path(output_dir) if output_dir else self.config.SAMPLES_DIR
        self.output_dir.mkdir(exist_ok=True)

    def generate_csv_sample(
        self, filename: str = "sample_data.csv", rows: int = 100
    ) -> Path:
        """Generate a comprehensive sample CSV file with various data types."""
        # Generate realistic sample data
        names = [
            "Alice Johnson",
            "Bob Smith",
            "Charlie Brown",
            "Diana Prince",
            "Eve Davis",
            "Frank Miller",
            "Grace Wilson",
            "Henry Garcia",
            "Ivy Martinez",
            "Jack Taylor",
            "Karen Anderson",
            "Leo Thompson",
            "Mia Rodriguez",
            "Noah Lewis",
            "Olivia Clark",
        ]

        companies = [
            "Acme Corp",
            "Beta Industries",
            "Gamma Solutions",
            "Delta Systems",
            "Epsilon Technologies",
            "Zeta Enterprises",
            "Eta Innovations",
            "Theta Labs",
        ]

        # Generate sample data with various data types for testing different anonymization methods
        df = pd.DataFrame(
            {
                "EmployeeID": range(1, rows + 1),
                "Name": np.random.choice(names, rows),
                "Age": np.random.randint(22, 65, rows),
                "Email": [
                    f"{name.lower().replace(' ', '.')}{i}@{company.lower().replace(' ', '')}.com"
                    for i, (name, company) in enumerate(
                        zip(
                            np.random.choice(names, rows),
                            np.random.choice(companies, rows),
                        )
                    )
                ],
                "Phone": [
                    f"({np.random.randint(200, 999)}) {np.random.randint(200, 999)}-{np.random.randint(1000, 9999)}"
                    for _ in range(rows)
                ],
                "SSN": [
                    f"{np.random.randint(100, 999)}-{np.random.randint(10, 99)}-{np.random.randint(1000, 9999)}"
                    for _ in range(rows)
                ],
                "Company": np.random.choice(companies, rows),
                "Department": np.random.choice(
                    [
                        "Engineering",
                        "Marketing",
                        "Sales",
                        "HR",
                        "Finance",
                        "Operations",
                    ],
                    rows,
                ),
                "Salary": np.random.randint(40000, 150000, rows),
                "HireDate": pd.date_range(
                    start="2020-01-01", end="2023-12-31", periods=rows
                ).strftime("%Y-%m-%d"),
                "City": np.random.choice(
                    [
                        "New York",
                        "Los Angeles",
                        "Chicago",
                        "Houston",
                        "Phoenix",
                        "Philadelphia",
                        "San Antonio",
                        "San Diego",
                        "Dallas",
                        "San Jose",
                    ],
                    rows,
                ),
                "State": np.random.choice(
                    ["NY", "CA", "IL", "TX", "AZ", "PA", "TX", "CA", "TX", "CA"], rows
                ),
                "CreditScore": np.random.randint(300, 850, rows),
                "AnnualBonus": np.random.randint(0, 25000, rows),
                "ProjectCount": np.random.randint(1, 15, rows),
            }
        )

        output_path = self.output_dir / filename
        df.to_csv(output_path, index=False)
        return output_path

    def generate_excel_sample(self, filename: str = "sample_multisheet.xlsx") -> Path:
        """Generate a comprehensive sample Excel file with multiple sheets."""
        # Employees sheet with sensitive data
        employees = pd.DataFrame(
            {
                "EmployeeID": range(1, 51),
                "Name": np.random.choice(
                    [
                        "Alice Johnson",
                        "Bob Smith",
                        "Charlie Brown",
                        "Diana Prince",
                        "Eve Davis",
                        "Frank Miller",
                        "Grace Wilson",
                        "Henry Garcia",
                        "Ivy Martinez",
                        "Jack Taylor",
                    ],
                    50,
                ),
                "Age": np.random.randint(22, 65, 50),
                "DateOfBirth": pd.date_range(
                    start="1960-01-01", end="2000-12-31", periods=50
                ).strftime("%Y-%m-%d"),
                "Email": [f"employee{i}@company.com" for i in range(1, 51)],
                "Phone": [
                    f"({np.random.randint(200, 999)}) {np.random.randint(200, 999)}-{np.random.randint(1000, 9999)}"
                    for _ in range(50)
                ],
                "SSN": [
                    f"{np.random.randint(100, 999)}-{np.random.randint(10, 99)}-{np.random.randint(1000, 9999)}"
                    for _ in range(50)
                ],
                "Department": np.random.choice(
                    [
                        "Engineering",
                        "Marketing",
                        "Sales",
                        "HR",
                        "Finance",
                        "Operations",
                    ],
                    50,
                ),
                "Salary": np.random.randint(40000, 150000, 50),
                "HireDate": pd.date_range(
                    start="2015-01-01", end="2023-12-31", periods=50
                ).strftime("%Y-%m-%d"),
                "Manager": np.random.choice(
                    ["John Doe", "Jane Smith", "Mike Johnson", "Sarah Williams"], 50
                ),
                "Address": [
                    f"{np.random.randint(1, 9999)} {np.random.choice(['Main', 'Oak', 'First', 'Second', 'Park'])} St, City {i}"
                    for i in range(1, 51)
                ],
                "EmergencyContact": [f"Contact{i}@family.com" for i in range(1, 51)],
            }
        )

        # Customer data sheet
        customers = pd.DataFrame(
            {
                "CustomerID": range(1, 101),
                "Name": np.random.choice(
                    [
                        "John Anderson",
                        "Jane Williams",
                        "Mike Brown",
                        "Sarah Davis",
                        "Tom Wilson",
                        "Lisa Johnson",
                        "David Miller",
                        "Emily Garcia",
                        "Chris Martinez",
                        "Anna Taylor",
                    ],
                    100,
                ),
                "Email": [f"customer{i}@email.com" for i in range(1, 101)],
                "Phone": [
                    f"({np.random.randint(200, 999)}) {np.random.randint(200, 999)}-{np.random.randint(1000, 9999)}"
                    for _ in range(100)
                ],
                "Address": [
                    f"{np.random.randint(1, 9999)} {np.random.choice(['Main', 'Oak', 'First', 'Second', 'Park'])} St, City {i}"
                    for i in range(1, 101)
                ],
                "City": np.random.choice(
                    ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"], 100
                ),
                "State": np.random.choice(["NY", "CA", "IL", "TX", "AZ"], 100),
                "ZipCode": [f"{np.random.randint(10000, 99999)}" for _ in range(100)],
                "CreditScore": np.random.randint(300, 850, 100),
                "AnnualIncome": np.random.randint(30000, 200000, 100),
                "AccountBalance": np.round(np.random.uniform(100, 50000, 100), 2),
                "LastPurchaseDate": pd.date_range(
                    start="2023-01-01", end="2023-12-31", periods=100
                ).strftime("%Y-%m-%d"),
            }
        )

        # Financial transactions sheet
        transactions = pd.DataFrame(
            {
                "TransactionID": range(1, 201),
                "CustomerID": np.random.randint(1, 101, 200),
                "Amount": np.round(np.random.uniform(10, 5000, 200), 2),
                "TransactionDate": pd.date_range(
                    start="2023-01-01", end="2023-12-31", periods=200
                ).strftime("%Y-%m-%d"),
                "TransactionType": np.random.choice(
                    ["Purchase", "Refund", "Transfer", "Payment"], 200
                ),
                "MerchantName": np.random.choice(
                    ["Amazon", "Walmart", "Target", "Best Buy", "Costco"], 200
                ),
                "Category": np.random.choice(
                    ["Electronics", "Groceries", "Clothing", "Entertainment", "Travel"],
                    200,
                ),
                "PaymentMethod": np.random.choice(
                    ["Credit Card", "Debit Card", "PayPal", "Bank Transfer"], 200
                ),
                "Location": np.random.choice(
                    ["New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX"],
                    200,
                ),
            }
        )

        output_path = self.output_dir / filename
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            employees.to_excel(writer, sheet_name="Employees", index=False)
            customers.to_excel(writer, sheet_name="Customers", index=False)
            transactions.to_excel(writer, sheet_name="Transactions", index=False)

        return output_path

    def generate_all_samples(self) -> dict:
        """Generate all sample files."""
        results = {}

        try:
            csv_path = self.generate_csv_sample()
            results["csv"] = str(csv_path)
            print(f"Generated CSV sample: {csv_path}")
        except Exception as e:
            results["csv"] = f"Error: {e}"

        try:
            excel_path = self.generate_excel_sample()
            results["excel"] = str(excel_path)
            print(f"Generated Excel sample: {excel_path}")
        except Exception as e:
            results["excel"] = f"Error: {e}"

        return results


def generate_sample_data(output_dir: Optional[str] = None) -> dict:
    """Generate sample data files (convenience function)."""
    generator = SampleDataGenerator(output_dir)
    return generator.generate_all_samples()


if __name__ == "__main__":
    # For Docker environment
    if os.environ.get("DOCKER_ENV"):
        output_dir = "/app/samples"
    else:
        output_dir = None

    results = generate_sample_data(output_dir)
    print("Sample data generation results:")
    for file_type, result in results.items():
        print(f"  {file_type}: {result}")
