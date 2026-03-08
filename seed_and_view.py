import time
import requests
import json
import os

BASE_URL = "http://localhost:8000/api/v1"

def wait_for_backend():
    print("Waiting for backend to be ready...")
    for _ in range(30):
        try:
            response = requests.get("http://localhost:8000/docs")
            if response.status_code == 200:
                print("Backend is ready.")
                return
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    print("Backend did not start in time.")
    exit(1)

def main():
    wait_for_backend()

    print("\n--- 1. Creating Account ---")
    res = requests.post(f"{BASE_URL}/accounts", json={"name": "Test Account"})
    res.raise_for_status()
    account_id = res.json()["id"]
    print(f"Created Account ID: {account_id}")

    print("\n--- 2. Creating Part ---")
    res = requests.post(f"{BASE_URL}/parts", json={
        "account_id": account_id,
        "name": "Box part",
        "description": "A simple box"
    })
    res.raise_for_status()
    part_id = res.json()["id"]
    print(f"Created Part ID: {part_id}")

    print("\n--- 3. Creating Part Revision ---")
    res = requests.post(f"{BASE_URL}/part-revisions", json={
        "part_id": part_id,
        "revision_number": 1
    })
    res.raise_for_status()
    rev_id = res.json()["id"]
    print(f"Created Part Revision ID: {rev_id}")

    print("\n--- 4. Uploading File ---")
    with open("box.glb", "wb") as f:
        f.write(b"glTF dummy content")
    
    with open("box.glb", "rb") as f:
        files = {"file": ("box.glb", f, "model/gltf-binary")}
        data = {"part_revision_id": str(rev_id)}
        res = requests.post(f"{BASE_URL}/files", data=data, files=files)
        res.raise_for_status()
        file_id = res.json()["id"]
        print(f"Uploaded File ID: {file_id}")

    print("\n--- 5. Triggering Conversion ---")
    res = requests.post(f"{BASE_URL}/convert", json={
        "file_id": str(file_id),
        "quality": "high"
    })
    res.raise_for_status()
    job_id = res.json()["job_id"]
    print(f"Conversion Job ID: {job_id}")
    
    # Wait for conversion
    for _ in range(5):
        time.sleep(1)
        res = requests.get(f"{BASE_URL}/jobs/{job_id}")
        if res.status_code == 200:
            status = res.json()["status"]
            print(f"Job Status: {status}")
            if status == "completed":
                break

    print("\n--- 6. Creating Scene ---")
    res = requests.post(f"{BASE_URL}/scenes", json={
        "account_id": account_id,
        "name": "My First Scene"
    })
    res.raise_for_status()
    scene_id = res.json()["id"]
    print(f"Created Scene ID: {scene_id}")

    print("\n--- 7. Adding Part to Scene ---")
    res = requests.post(f"{BASE_URL}/scenes/{scene_id}/items", json={
        "part_revision_id": rev_id
    })
    res.raise_for_status()
    print("Added part revision to scene.")

    print(f"\n==============================================")
    print(f"SUCCESS! Open viewer to connect to SCENE ID: {scene_id}")
    print(f"==============================================")

if __name__ == "__main__":
    main()
