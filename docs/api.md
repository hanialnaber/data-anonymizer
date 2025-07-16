# API Documentation

## Overview

The Data Anonymizer API provides RESTful endpoints for anonymizing sensitive data in CSV and Excel files.

Base URL: `http://localhost:8000/api/v1`

## Authentication

Currently, the API does not require authentication. In production, consider implementing appropriate authentication mechanisms.

## Endpoints

### POST /anonymize

Anonymize data in a file.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/anonymize" \
  -F "filename=path/to/file.csv" \
  -F "output_format=csv" \
  -F "masking_config={\"Sheet1\": {\"name\": \"hash\", \"email\": \"substitute\"}}" \
  -F "ml_columns_config={}"
```

**Parameters:**
- `filename` (required): Path to the input file
- `output_format` (required): Output format (csv, xlsx)
- `masking_config` (required): JSON string with anonymization configuration
- `ml_columns_config` (required): JSON string with ML column configuration
- `selected_sheet` (optional): Specific sheet name for Excel files

**Response:**
```json
{
  "status": "processing",
  "message": "Anonymization job started",
  "result_file": "anonymized_file.csv"
}
```

### GET /status

Get API status information.

**Response:**
```json
{
  "status": "running",
  "version": "0.1.0",
  "samples_dir": "/path/to/samples"
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## Anonymization Methods

### Hash
Replaces values with SHA-256 hashes.

```json
{
  "Sheet1": {
    "column_name": "hash"
  }
}
```

### Shuffle
Randomly reorders values within the column.

```json
{
  "Sheet1": {
    "column_name": "shuffle"
  }
}
```

### Substitute
Replaces values with predefined substitutions.

```json
{
  "Sheet1": {
    "column_name": "substitute"
  }
}
```

### Perturb
Adds random noise to numerical values.

```json
{
  "Sheet1": {
    "column_name": "perturb"
  }
}
```

## Error Handling

The API uses standard HTTP status codes:

- `200`: Success
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

Error responses include a `detail` field with more information:

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. Consider adding rate limiting for production deployments.

## Examples

### Python Example

```python
import requests

# Anonymize a CSV file
response = requests.post(
    "http://localhost:8000/api/v1/anonymize",
    data={
        "filename": "employee_data.csv",
        "output_format": "csv",
        "masking_config": json.dumps({
            "Sheet1": {
                "name": "hash",
                "email": "substitute",
                "salary": "perturb"
            }
        }),
        "ml_columns_config": "{}"
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"Processing started. Result file: {result['result_file']}")
else:
    print(f"Error: {response.json()}")
```

### JavaScript Example

```javascript
const formData = new FormData();
formData.append('filename', 'employee_data.csv');
formData.append('output_format', 'csv');
formData.append('masking_config', JSON.stringify({
    "Sheet1": {
        "name": "hash",
        "email": "substitute"
    }
}));
formData.append('ml_columns_config', '{}');

fetch('http://localhost:8000/api/v1/anonymize', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```
