"""
Tests for 100-Document Border Stream Benchmark & Simulation Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_get_benchmark_100_endpoint():
    response = client.get("/api/dashboard/benchmark-100?seed=42")
    assert response.status_code == 200
    data = response.json()
    assert data["total_documents"] == 100
    assert data["passed_count"] == 68
    assert data["failed_count"] == 32
    assert len(data["documents"]) == 100
    
    # Check 4 modules exist in document
    first_doc = data["documents"][0]
    assert "modules" in first_doc
    assert "ocr" in first_doc["modules"]
    assert "validation" in first_doc["modules"]
    assert "tampering" in first_doc["modules"]
    assert "face" in first_doc["modules"]
    assert "sample_checks" in first_doc
    assert len(first_doc["sample_checks"]) > 0

def test_run_benchmark_100_post_endpoint():
    response = client.post("/api/dashboard/benchmark-100/run")
    assert response.status_code == 200
    data = response.json()
    assert data["total_documents"] == 100
    assert data["passed_count"] == 68
    assert data["failed_count"] == 32
