# Data Anonymizer Stop Script for PowerShell
Write-Host "Stopping Data Anonymizer Application..." -ForegroundColor Yellow
Get-Process | Where-Object { $_.ProcessName -like "*uvicorn*" -or $_.ProcessName -like "*streamlit*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Job | Stop-Job -PassThru | Remove-Job
Write-Host "Application stopped." -ForegroundColor Green
