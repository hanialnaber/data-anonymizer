@echo off 
echo Stopping Data Anonymizer Application... 
taskkill /f /im python.exe 2>nul || echo No Python processes found 
taskkill /f /im uvicorn.exe 2>nul || echo FastAPI not running 
taskkill /f /im streamlit.exe 2>nul || echo Streamlit not running 
echo Application stopped. 
pause 
