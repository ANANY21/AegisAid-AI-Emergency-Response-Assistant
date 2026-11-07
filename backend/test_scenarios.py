"""
AegisAid - Emergency Triage Scenarios & Verification Suite
==========================================================
Tests core emergency triage scenarios directly via FastAPI TestClient
to ensure production readiness on Railway.
"""

import sys
import os
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

SCENARIOS = [
    {
        "name": "Cardiac Arrest Emergency",
        "payload": {
            "description": "Adult patient suddenly collapsed, unresponsive, not breathing normally, only gasping faintly.",
            "input_type": "text",
            "patient_age": 58,
            "duration": "3 minutes"
        },
        "expected_priorities": ["CRITICAL"],
        "expect_warning": True
    },
    {
        "name": "Suspected Acute Stroke",
        "payload": {
            "description": "Grandmother suddenly has severe facial droop on left side, cannot lift left arm, speech is slurred and confused.",
            "input_type": "text",
            "patient_age": 72,
            "duration": "25 minutes"
        },
        "expected_priorities": ["CRITICAL"],
        "expect_warning": True
    },
    {
        "name": "Severe Airway Choking",
        "payload": {
            "description": "Adult choking on steak at dinner, cannot speak, silent cough, hands clutched around neck, lips turning blue.",
            "input_type": "text",
            "patient_age": 44,
            "duration": "2 minutes"
        },
        "expected_priorities": ["CRITICAL"],
        "expect_warning": True
    },
    {
        "name": "Boiling Water Scald Burn",
        "payload": {
            "description": "Spilled pot of boiling water over hand and forearm. Severe intense pain, skin is bright red with large fluid blisters.",
            "input_type": "text",
            "patient_age": 26,
            "duration": "10 minutes"
        },
        "expected_priorities": ["HIGH", "MODERATE"],
        "expect_warning": False
    },
    {
        "name": "Ambiguous / Incomplete Input",
        "payload": {
            "description": "I feel slightly sick and my body hurts all over.",
            "input_type": "text",
            "patient_age": 30,
            "duration": "unknown"
        },
        "expected_priorities": ["LOW", "MODERATE", "HIGH", "CRITICAL"],
        "expect_warning": False
    }
]

def run_all_scenarios():
    print("=" * 70)
    print("AegisAid - Verification of Emergency Scenarios")
    print("=" * 70)
    
    # 1. Health check
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
    print(f"[PASS] Health Check OK: {health_resp.json()['service']} v{health_resp.json()['version']}")

    passed = 0
    total = len(SCENARIOS)

    for idx, s in enumerate(SCENARIOS, 1):
        print(f"\n[{idx}/{total}] Testing Scenario: {s['name']}...")
        resp = client.post("/api/emergency/analyze", json=s["payload"])
        
        if resp.status_code != 200:
            print(f"  [FAIL]: HTTP {resp.status_code} - {resp.text}")
            continue
            
        data = resp.json()
        priority = data.get("priority")
        outcome = data.get("outcome")
        steps = data.get("first_aid_steps", [])
        
        print(f"  [OK] Outcome: {outcome}")
        print(f"  [OK] Priority: {priority}")
        print(f"  [OK] First Aid Steps Count: {len(steps)}")
        
        if priority in s["expected_priorities"]:
            print(f"  [PASS] Correct priority match: {priority}")
            passed += 1
        else:
            print(f"  [FAIL] Priority mismatch! Got {priority}, expected {s['expected_priorities']}")

    print("\n" + "=" * 70)
    print(f"Scenario Verification Results: {passed}/{total} Passed")
    print("=" * 70)
    return passed == total

if __name__ == "__main__":
    success = run_all_scenarios()
    sys.exit(0 if success else 1)
