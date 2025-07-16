"""Streamlit frontend for Data Anonymizer."""

import streamlit as st
import requests
import json
import os
import pandas as pd
import io

# Configure page
st.set_page_config(
    page_title="Data Anonymizer", 
    page_icon="🔒",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_BASE_URL = f"{BACKEND_URL}/api/v1"

def get_file_type(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".csv":
        return "csv"
    elif ext == ".xlsx":
        return "xlsx"
    return None

def ensure_samples_exist():
    """Ensure sample files exist by generating them if needed."""
    try:
        # Check if samples directory exists and has files
        samples_url = f"{BACKEND_URL}/api/v1/samples"
        response = requests.get(samples_url)
        if response.status_code == 200:
            files = response.json()
            if not files:  # No sample files found
                # Generate samples
                generate_samples()
    except Exception as e:
        st.error(f"Error checking samples: {str(e)}")

def generate_samples():
    """Generate sample data files."""
    try:
        # Call backend to generate samples
        response = requests.post(f"{BACKEND_URL}/api/v1/generate-samples")
        if response.status_code == 200:
            st.success("Sample files generated!")
        else:
            st.error("Failed to generate samples")
    except Exception as e:
        st.error(f"Error generating samples: {str(e)}")

def get_sample_files_info():
    """Get information about available sample files."""
    sample_files = []
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/samples")
        if response.status_code == 200:
            files = response.json()
            
            # Add descriptions for each file
            file_descriptions = {
                "sample_data.csv": "Simple CSV with employee data (Name, Age, Email, Company, Salary, SSN)",
                "sample_multisheet.xlsx": "Excel file with multiple sheets (Employees, Inventory, Sales)",
            }
            
            for filename in files:
                sample_files.append({
                    "filename": filename,
                    "description": file_descriptions.get(filename, "Sample data file")
                })
    except Exception as e:
        st.error(f"Error loading sample files: {str(e)}")
    
    return sample_files

def import_sample_file(filename):
    """Import a sample file into the upload field."""
    try:
        # Download the sample file
        file_url = f"{BACKEND_URL}/samples/{filename}"
        response = requests.get(file_url)
        
        if response.status_code == 200:
            # Store the file content in session state
            st.session_state['imported_file'] = {
                'name': filename,
                'content': response.content,
                'type': get_file_type(filename)
            }
            st.success(f"✅ Imported {filename}")
        else:
            st.error(f"Failed to import {filename}")
    except Exception as e:
        st.error(f"Error importing {filename}: {str(e)}")

def download_sample_file(filename):
    """Download a sample file."""
    try:
        file_url = f"{BACKEND_URL}/samples/{filename}"
        response = requests.get(file_url)
        
        if response.status_code == 200:
            st.download_button(
                label=f"💾 Download {filename}",
                data=response.content,
                file_name=filename,
                key=f"download_btn_{filename}"
            )
        else:
            st.error(f"Failed to download {filename}")
    except Exception as e:
        st.error(f"Error downloading {filename}: {str(e)}")

def get_columns_and_sheets(uploaded_file, file_type):
    if file_type == "csv":
        try:
            file_bytes = uploaded_file.getvalue()
            # decode as text
            first_line = file_bytes.split(b"\n", 1)[0].decode("utf-8")
            columns = [c.strip() for c in first_line.split(",")]
            return {"Sheet1": columns}, "Sheet1"
        except Exception as e:
            st.error(f"Failed to read CSV file: {e}")
            return {}, None
    elif file_type == "xlsx":
        file_bytes = uploaded_file.getvalue()
        # Check for XLSX magic number (PK\x03\x04)
        if not file_bytes.startswith(b'PK'):
            st.error("The uploaded file is not a valid Excel (.xlsx) file.")
            return {}, None
        try:
            xls = pd.ExcelFile(io.BytesIO(file_bytes), engine="openpyxl")
            sheets_columns = {}
            for sheet in xls.sheet_names:
                df = xls.parse(sheet, nrows=1)
                sheets_columns[sheet] = list(df.columns)
            return sheets_columns, xls.sheet_names[0]
        except Exception as e:
            st.error(f"Failed to read Excel file: {e}")
            return {}, None
    else:
        st.error("Unsupported file type. Please upload a CSV or XLSX file.")
        return {}, None

def main():
    # Add application description at the top
    st.title("🔒 Data Anonymizer")
    st.markdown("""
    **Welcome to the Data Anonymizer Application!**
    
    This tool helps you anonymize sensitive data in CSV and Excel files using various anonymization techniques:
    
    - **Hash**: Replace values with one-way cryptographic hashes
    - **Substitute**: Replace values with random items from predefined lists
    - **Shuffle**: Randomly reorder values within each column
    - **Perturb**: Add random noise to numerical values
    
    **How to use:**
    1. 📁 Upload your CSV or Excel file, or use one of the sample files below
    2. ⚙️ Configure anonymization methods for each column
    3. 🚀 Click "Anonymize" to process your data
    4. 📥 Download the anonymized result
    
    ---
    """)
    
    # Sample Data Files Section (moved to main UI)
    st.header("📂 Sample Data Files")
    st.markdown("*Try the application with sample data - click to import directly*")
    
    # Generate samples at startup if they don't exist
    ensure_samples_exist()
    
    # Get available sample files
    sample_files_info = get_sample_files_info()
    
    # Display sample files with import buttons in main UI
    if sample_files_info:
        # Create columns for better layout
        cols = st.columns(len(sample_files_info))
        
        for i, file_info in enumerate(sample_files_info):
            fname = file_info["filename"]
            description = file_info["description"]
            
            with cols[i]:
                st.subheader(f"📄 {fname}")
                st.caption(description)
                
                # Create two columns for buttons
                btn_col1, btn_col2 = st.columns(2)
                
                with btn_col1:
                    if st.button(f"📥 Import", key=f"import_{fname}", help=f"Import {fname} for processing"):
                        import_sample_file(fname)
                
                with btn_col2:
                    if st.button(f"💾 Download", key=f"download_{fname}", help=f"Download {fname}"):
                        download_sample_file(fname)
    else:
        st.info("No sample files available. They will be generated automatically when needed.")
    
    st.markdown("---")
    
    # File Upload Section
    st.header("📁 Upload Data File")
    
    # Check if a file was imported from samples
    imported_file = st.session_state.get('imported_file', None)
    
    if imported_file:
        st.info(f"📂 **Imported file:** {imported_file['name']}")
        if st.button("❌ Clear imported file"):
            del st.session_state['imported_file']
            st.rerun()
        
        # Use imported file
        file_content = imported_file['content']
        file_name = imported_file['name']
        file_type = imported_file['type']
        
        # Create a file-like object for processing
        class ImportedFile:
            def __init__(self, content, name):
                self.content = content
                self.name = name
            
            def getvalue(self):
                return self.content
        
        uploaded_file = ImportedFile(file_content, file_name)
        
    else:
        uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=['csv', 'xlsx'])
        file_type = get_file_type(uploaded_file.name) if uploaded_file else None

    sheets_columns = {}
    selected_sheet = None
    columns = []
    if uploaded_file:
        st.write(f"**Selected file:** {uploaded_file.name}")
        if not imported_file:  # Only get file type if not imported
            file_type = get_file_type(uploaded_file.name)
        sheets_columns, default_sheet = get_columns_and_sheets(uploaded_file, file_type)
        if sheets_columns:
            if file_type == "xlsx":
                selected_sheet = st.selectbox("Select Sheet", list(sheets_columns.keys()), index=0)
            else:
                selected_sheet = "Sheet1"
            columns = sheets_columns[selected_sheet]
        else:
            columns = []
            selected_sheet = None
    else:
        columns = []
        selected_sheet = None
        sheets_columns = {}

    masking_config = {}
    if sheets_columns:
        for sheet, cols in sheets_columns.items():
            st.subheader(f"Configure Anonymization for Sheet: {sheet}")
            
            # Add explanation
            st.info("""
            **Enhanced Anonymization Methods:**
            - **None**: No anonymization applied
            - **Hash**: Replace values with one-way cryptographic hash (SHA-256)
            - **Mask**: Replace characters with asterisks (e.g., John → J**n)
            - **Pseudonymize**: Replace with consistent pseudonyms (e.g., John → ID_a1b2c3d4)
            - **Substitute**: Replace with random values from predefined lists
            - **Shuffle**: Randomly shuffle values within the column
            - **Perturb**: Add random noise to numerical values
            - **Generalize Numeric**: Group numbers into ranges (e.g., 25 → 20-29)
            - **Generalize Date**: Reduce date precision (e.g., 2023-12-15 → 2023-12)
            - **Anonymize Email**: Anonymize email addresses while preserving structure
            - **Anonymize Phone**: Anonymize phone numbers while preserving format
            - **Anonymize SSN**: Anonymize Social Security Numbers
            - **K-Anonymity**: Suppress values that appear less than k times
            - **Differential Privacy**: Add statistical noise for privacy protection
            - **Remove**: Completely remove the column from output
            """)
            
            # Available anonymization methods
            anonymization_methods = [
                "None", "Hash", "Mask", "Pseudonymize", "Substitute", "Shuffle", 
                "Perturb", "Generalize Numeric", "Generalize Date", "Anonymize Email",
                "Anonymize Phone", "Anonymize SSN", "K-Anonymity", "Differential Privacy", "Remove"
            ]
            
            # Create configuration data for the table
            config_data = []
            masking_logic = {}
            
            # Create table configuration
            for col in cols:
                config_data.append({
                    "Column": col,
                    "Anonymization Method": "None"
                })
            
            # Display the configuration as an editable table
            st.write("**Anonymization Configuration:**")
            st.write("---")
            
            # Create columns for the table layout
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.write("**Column Name**")
            with col2:
                st.write("**Anonymization Method**")
            
            st.write("---")
            
            # Create the interactive table
            for i, col in enumerate(cols):
                # Add alternating row colors effect with containers
                if i % 2 == 0:
                    container = st.container()
                else:
                    container = st.container()
                
                with container:
                    col1, col2 = st.columns([3, 2])
                    
                    with col1:
                        st.write(f"`{col}`")
                    
                    with col2:
                        method = st.selectbox(
                            f"Method for {col}",
                            anonymization_methods,
                            key=f"method_{sheet}_{col}",
                            label_visibility="collapsed",
                            help=f"Select anonymization method for column '{col}'"
                        )
                        if method != "None":
                            # Convert method name to lowercase and replace spaces with underscores
                            method_key = method.lower().replace(" ", "_")
                            masking_logic[col] = method_key
            
            st.write("---")
            
            masking_config[sheet] = masking_logic
            
            # Show summary of configuration
            if masking_logic:
                st.write("**Configuration Summary:**")
                st.write(f"📝 **Columns to anonymize:** {', '.join(masking_logic.keys())}")
                for col, method in masking_logic.items():
                    st.write(f"  - `{col}`: {method.title()}")
            else:
                st.write("ℹ️ No anonymization configured for this sheet")

    if st.button("Anonymize") and uploaded_file and selected_sheet:
        with st.spinner("Starting anonymization..."):
            file_type = get_file_type(uploaded_file.name)
            data = {
                "filename": uploaded_file.name,
                "output_format": file_type,
                "masking_config": json.dumps(masking_config),
                "selected_sheet": selected_sheet,
            }
            
            # Check if it's an imported file (already exists on server)
            if imported_file:
                # For imported files, we don't need to upload again
                r = requests.post(f"{BACKEND_URL}/api/v1/anonymize/", data=data)
            else:
                # For uploaded files, upload first then anonymize
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                upload_resp = requests.post(f"{BACKEND_URL}/api/v1/upload/", files=files)
                if upload_resp.status_code != 200:
                    st.error(f"Upload failed: {upload_resp.text}")
                    return
                r = requests.post(f"{BACKEND_URL}/api/v1/anonymize/", data=data)
            
            if r.status_code == 200:
                result_file = r.json().get("result_file")
                st.success("Anonymization started!")
                st.session_state["result_file"] = result_file
            else:
                st.error(f"Anonymization failed: {r.text}")

    if "result_file" in st.session_state:
        result_file = st.session_state["result_file"]
        st.info(f"Result file: {result_file}")
        if st.button("Download Anonymized File"):
            with st.spinner("Downloading..."):
                r = requests.get(f"{BACKEND_URL}/api/v1/download/{result_file}")
                if r.status_code == 200:
                    st.download_button(
                        label="Download File",
                        data=r.content,
                        file_name=result_file
                    )
                else:
                    st.error("Download failed.")

if __name__ == "__main__":
    main()
