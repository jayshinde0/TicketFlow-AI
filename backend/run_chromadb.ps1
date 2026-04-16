# PowerShell script to run ChromaDB server on port 8001
# This allows the backend to connect to ChromaDB via HTTP instead of using local storage

Write-Host "Starting ChromaDB server on port 8001..." -ForegroundColor Green
chroma run --host localhost --port 8001 --path ./chroma_data
