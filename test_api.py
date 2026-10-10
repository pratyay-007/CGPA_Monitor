"""
Test script to verify BPUT API endpoints work correctly.
Tests with sample registration numbers: 2401289308, 2401289285
"""

import requests
import json
import time

BASE_URL = "https://results.bput.ac.in"
DOB = "2000-01-01"  # Any DOB works according to PROGRESS.md

HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://results.bput.ac.in/",
    "Origin": "https://results.bput.ac.in",
}


def test_results_list(roll_no, session):
    """Test the student-results-list endpoint."""
    url = f"{BASE_URL}/student-results-list?rollNo={roll_no}&dob={DOB}&session={session}"
    print(f"\n{'='*60}")
    print(f"Testing: student-results-list")
    print(f"URL: {url}")
    
    resp = requests.post(url, headers=HEADERS)
    print(f"Status: {resp.status_code}")
    
    try:
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        print(f"Response text: {resp.text[:500]}")
        return None


def test_student_details(roll_no):
    """Test the student-detsils-results endpoint (note: typo is in the original API)."""
    url = f"{BASE_URL}/student-detsils-results?rollNo={roll_no}"
    print(f"\n{'='*60}")
    print(f"Testing: student-detsils-results")
    print(f"URL: {url}")
    
    resp = requests.post(url, headers=HEADERS)
    print(f"Status: {resp.status_code}")
    
    try:
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        print(f"Response text: {resp.text[:500]}")
        return None


def test_subjects_list(roll_no, sem, session):
    """Test the student-results-subjects-list endpoint."""
    url = f"{BASE_URL}/student-results-subjects-list?semid={sem}&rollNo={roll_no}&session={session}"
    print(f"\n{'='*60}")
    print(f"Testing: student-results-subjects-list")
    print(f"URL: {url}")
    
    resp = requests.post(url, headers=HEADERS)
    print(f"Status: {resp.status_code}")
    
    try:
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        print(f"Response text: {resp.text[:500]}")
        return None


def test_sgpa(roll_no, sem, session):
    """Test the student-results-sgpa endpoint."""
    url = f"{BASE_URL}/student-results-sgpa?rollNo={roll_no}&semid={sem}&session={session}"
    print(f"\n{'='*60}")
    print(f"Testing: student-results-sgpa")
    print(f"URL: {url}")
    
    resp = requests.post(url, headers=HEADERS)
    print(f"Status: {resp.status_code}")
    
    try:
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        print(f"Response text: {resp.text[:500]}")
        return None


if __name__ == "__main__":
    test_roll = "2401289308"
    test_session = "Odd-(2024-25)"  # Semester 1
    
    print(f"Testing BPUT API with roll number: {test_roll}")
    print(f"Session: {test_session}")
    
    # Step 1: Get results list
    results = test_results_list(test_roll, test_session)
    time.sleep(2)
    
    # Step 2: Get student details
    details = test_student_details(test_roll)
    time.sleep(2)
    
    # Step 3: Get subjects for semester 1
    if results and isinstance(results, list) and len(results) > 0:
        sem = results[0].get("sem", "1st")
        print(f"\nUsing semester: {sem}")
        subjects = test_subjects_list(test_roll, sem, test_session)
        time.sleep(2)
        
        # Step 4: Get SGPA
        sgpa = test_sgpa(test_roll, sem, test_session)
    else:
        print("\nNo results found, trying with sem='1st'")
        subjects = test_subjects_list(test_roll, "1st", test_session)
        time.sleep(2)
        sgpa = test_sgpa(test_roll, "1st", test_session)
    
    print(f"\n{'='*60}")
    print("Test complete!")
