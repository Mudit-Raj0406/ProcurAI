"""Quick verification script: test signup, login, and Mistral LLM call."""
import requests
import json
import time
import sys
import os

# Force UTF-8 output
os.environ["PYTHONIOENCODING"] = "utf-8"

BASE = "http://127.0.0.1:8001"

print("=" * 60)
print("TEST 1: Signup")
print("=" * 60)
signup_data = {
    "email": f"testuser_{int(time.time())}@example.com",
    "password": "TestPass123!",
    "full_name": "Test User",
    "role": "buyer"
}
r = requests.post(f"{BASE}/auth/signup", json=signup_data)
print(f"  Status: {r.status_code}")
print(f"  Response: {r.json()}")
assert r.status_code == 200, f"Signup failed: {r.text}"
print("  [PASS] Signup PASSED\n")

print("=" * 60)
print("TEST 2: Login (get token)")
print("=" * 60)
login_data = {
    "username": signup_data["email"],
    "password": signup_data["password"]
}
r = requests.post(f"{BASE}/auth/token", data=login_data)
print(f"  Status: {r.status_code}")
resp = r.json()
print(f"  Response: {resp}")
assert r.status_code == 200, f"Login failed: {r.text}"
assert "access_token" in resp, "No access_token in response"
token = resp["access_token"]
print(f"  Token: {token[:30]}...")
print("  [PASS] Login PASSED\n")

print("=" * 60)
print("TEST 3: Get current user (/auth/me)")
print("=" * 60)
r = requests.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {token}"})
print(f"  Status: {r.status_code}")
print(f"  Response: {r.json()}")
assert r.status_code == 200, f"/auth/me failed: {r.text}"
print("  [PASS] /auth/me PASSED\n")

print("=" * 60)
print("TEST 4: Duplicate signup (should fail)")
print("=" * 60)
r = requests.post(f"{BASE}/auth/signup", json=signup_data)
print(f"  Status: {r.status_code}")
print(f"  Response: {r.json()}")
assert r.status_code == 400, f"Duplicate signup should return 400, got {r.status_code}"
print("  [PASS] Duplicate signup correctly rejected\n")

print("=" * 60)
print("TEST 5: Mistral LLM quick call")
print("=" * 60)
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from dotenv import load_dotenv
    load_dotenv()
    from services.llm_extractor import call_mistral
    result = call_mistral("Say hello in one sentence.", instructions="You are a helpful assistant.")
    print(f"  LLM Response: {result}")
    assert len(result) > 0, "Empty LLM response"
    print("  [PASS] Mistral LLM PASSED\n")
except Exception as e:
    print(f"  [FAIL] Mistral LLM FAILED: {e}\n")
    import traceback
    traceback.print_exc()

print("=" * 60)
print("ALL TESTS COMPLETED")
print("=" * 60)
