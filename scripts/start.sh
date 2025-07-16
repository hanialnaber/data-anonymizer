#!/bin/bash
# Start FastAPI backend in the background
python -m uvicorn src.data_anonymizer.api.main:app --host 0.0.0.0 --port 8000 &
# Wait for backend to be ready
sleep 5
# Start Streamlit app, pointing to backend
streamlit run frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
