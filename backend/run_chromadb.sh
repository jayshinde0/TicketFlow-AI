#!/bin/bash
# Run ChromaDB server on port 8001
# This allows the backend to connect to ChromaDB via HTTP instead of using local storage

echo "Starting ChromaDB server on port 8001..."
chroma run --host localhost --port 8001 --path ./chroma_data
