#!/usr/bin/env python
"""
Simple script to test the affiliation check endpoint.
"""

import sys
import django
import os

# Setup Django
sys.path.insert(0, '/home/alejo/connectivity/project_connectivity')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
import requests

# Create or get test user
user, created = User.objects.get_or_create(
    username='testuser',
    defaults={'email': 'test@example.com'}
)
if created:
    user.set_password('testpass123')
    user.save()
    print(f"✅ Created test user: {user.username}")
else:
    print(f"✅ Using existing user: {user.username}")

# Generate JWT token
refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)

print(f"\n🔑 JWT Access Token:")
print(f"{access_token[:50]}...")

# Test the endpoint
print("\n" + "="*80)
print("📡 Testing Affiliation Check Endpoint")
print("="*80)

# Test Case 1: Valid citizen (should exist in Govcarpeta)
print("\n1️⃣  Testing with citizen_id: 1128456232")
try:
    response = requests.post(
        'http://localhost:8000/api/v1/affiliation/check/',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        },
        json={'citizen_id': '1128456232'},
        timeout=10
    )
    
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Citizen Status: {data.get('status')}")
        print(f"   ✅ Exists in System: {data.get('exists_in_system')}")
        print(f"   ✅ Is Eligible: {data.get('is_eligible')}")
        print(f"   ✅ Message: {data.get('message')}")
        if data.get('citizen_data'):
            print(f"   ✅ Citizen Data: {data.get('citizen_data')}")
    else:
        print(f"   ❌ Error: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("   ❌ Could not connect to server. Is the Django server running?")
    print("   💡 Run: python manage.py runserver")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test Case 2: Non-existent citizen (should return 204 from external API)
print("\n2️⃣  Testing with citizen_id: 9999999999 (should not exist)")
try:
    response = requests.post(
        'http://localhost:8000/api/v1/affiliation/check/',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        },
        json={'citizen_id': '9999999999'},
        timeout=10
    )
    
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Citizen Status: {data.get('status')}")
        print(f"   ✅ Exists in System: {data.get('exists_in_system')}")
        print(f"   ✅ Is Eligible: {data.get('is_eligible')}")
        print(f"   ✅ Message: {data.get('message')}")
    else:
        print(f"   ❌ Error: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("   ❌ Could not connect to server.")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test Case 3: Invalid citizen_id format
print("\n3️⃣  Testing with invalid citizen_id: ABC123")
try:
    response = requests.post(
        'http://localhost:8000/api/v1/affiliation/check/',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        },
        json={'citizen_id': 'ABC123'},
        timeout=10
    )
    
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 400:
        print(f"   ✅ Validation working correctly!")
        print(f"   ✅ Error details: {response.json()}")
    else:
        print(f"   ⚠️  Unexpected status code: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("   ❌ Could not connect to server.")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test Case 4: No authentication
print("\n4️⃣  Testing without authentication (should fail)")
try:
    response = requests.post(
        'http://localhost:8000/api/v1/affiliation/check/',
        headers={'Content-Type': 'application/json'},
        json={'citizen_id': '1128456232'},
        timeout=10
    )
    
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 401:
        print(f"   ✅ Authentication required - working correctly!")
    else:
        print(f"   ⚠️  Unexpected status code: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("   ❌ Could not connect to server.")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*80)
print("✅ Tests complete!")
print("="*80)
