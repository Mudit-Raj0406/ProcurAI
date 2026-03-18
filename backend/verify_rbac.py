import requests
import sys

BASE_URL = "http://127.0.0.1:8010"

def get_token(email, password):
    response = requests.post(f"{BASE_URL}/auth/token", data={"username": email, "password": password})
    if response.status_code != 200:
        print(f"Failed to login as {email}: {response.text}")
        return None
    return response.json()["access_token"]

def test_rbac():
    print("--- Starting RBAC Verification ---")
    
    # 1. Login
    sourcing_token = get_token("sourcing@example.com", "password123")
    procure_token = get_token("procure@example.com", "password123")
    
    if not sourcing_token or not procure_token:
        print("CRITICAL: Login failed. Is backend running?")
        return

    # 2. Test Project Upload (Sourcing Buyer - Should Succeed)
    headers_sourcing = {"Authorization": f"Bearer {sourcing_token}"}
    project_data = {"rfq_id": "TEST-RBAC-001", "title": "RBAC Test", "status": "Open"}
    
    print("\n[TEST] Sourcing Buyer creating project...")
    res = requests.post(f"{BASE_URL}/quotes/projects", json=project_data, headers=headers_sourcing)
    if res.status_code == 200:
        print("✅ Success (Expected)")
    else:
        print(f"❌ Failed: {res.status_code} {res.text}")

    # 3. Test Project Deletion (Sourcing Buyer - Should FAIL 403)
    print("\n[TEST] Sourcing Buyer deleting project...")
    res = requests.delete(f"{BASE_URL}/quotes/projects/TEST-RBAC-001", headers=headers_sourcing)
    if res.status_code == 403:
        print("✅ Blocked 403 (Expected)")
    else:
        print(f"❌ Unexpected: {res.status_code} {res.text}")

    # 4. Test Project Deletion (Procurement Manager - Should SUCCEED)
    headers_procure = {"Authorization": f"Bearer {procure_token}"}
    print("\n[TEST] Procurement Manager deleting project...")
    res = requests.delete(f"{BASE_URL}/quotes/projects/TEST-RBAC-001", headers=headers_procure)
    if res.status_code == 200:
        print("✅ Success (Expected)")
    else:
        print(f"❌ Failed: {res.status_code} {res.text}")

    print("\n--- RBAC Verification Complete ---")

if __name__ == "__main__":
    try:
        test_rbac()
    except Exception as e:
        print(f"Error: {e}")
