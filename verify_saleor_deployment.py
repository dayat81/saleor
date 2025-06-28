#!/usr/bin/env python3
"""
Saleor Cloud Deployment Verification Script
Verifies the Saleor GraphQL API is working correctly on Cloud Run
"""

import requests
import json
import sys
import subprocess
from typing import Dict, Any

# Your Cloud Run URL
SALEOR_URL = "https://saleor-app-hvodeun2nq-uc.a.run.app"
GRAPHQL_ENDPOINT = f"{SALEOR_URL}/graphql/"

def get_auth_token():
    """Get authentication token for Cloud Run"""
    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-identity-token"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("⚠️  Could not get authentication token")
        return None

def test_basic_connectivity() -> bool:
    """Test basic HTTP connectivity to the Saleor instance"""
    print("🔍 Testing basic connectivity...")
    token = get_auth_token()
    if not token:
        return False
        
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(SALEOR_URL, headers=headers, timeout=10)
        print(f"✅ HTTP Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_graphql_endpoint() -> bool:
    """Test GraphQL endpoint accessibility"""
    print("\n🔍 Testing GraphQL endpoint...")
    token = get_auth_token()
    if not token:
        return False
        
    try:
        # Test with a simple introspection query
        query = """
        query {
            __schema {
                queryType {
                    name
                }
            }
        }
        """
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.post(
            GRAPHQL_ENDPOINT,
            json={"query": query},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "__schema" in data["data"]:
                print("✅ GraphQL endpoint is accessible")
                print(f"✅ Query type: {data['data']['__schema']['queryType']['name']}")
                return True
            else:
                print(f"❌ GraphQL response error: {data}")
                return False
        else:
            print(f"❌ GraphQL endpoint returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ GraphQL request failed: {e}")
        return False

def test_products_query() -> bool:
    """Test products query with default channel"""
    print("\n🔍 Testing products query...")
    token = get_auth_token()
    if not token:
        return False
        
    try:
        query = """
        query {
            products(first: 5, channel: "default-channel") {
                edges {
                    node {
                        id
                        name
                        slug
                        category {
                            name
                        }
                    }
                }
            }
        }
        """
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.post(
            GRAPHQL_ENDPOINT,
            json={"query": query},
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "products" in data["data"]:
                products_data = data["data"]["products"]
                products = products_data["edges"] if products_data else []
                print(f"✅ Products query successful")
                print(f"✅ Found {len(products)} products")
                
                if products:
                    print("\n📦 Sample products:")
                    for product in products[:3]:
                        node = product["node"]
                        category = node.get("category", {}).get("name", "No category") if node.get("category") else "No category"
                        print(f"  - {node['name']} (Category: {category})")
                else:
                    print("ℹ️  No products found (this is normal for a fresh deployment)")
                
                return True
            else:
                print(f"❌ Products query error: {data}")
                return False
        else:
            print(f"❌ Products query returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Products query failed: {e}")
        return False

def test_channels_query() -> bool:
    """Test channels availability"""
    print("\n🔍 Testing channels...")
    token = get_auth_token()
    if not token:
        return False
        
    try:
        query = """
        query {
            channels {
                id
                name
                slug
                isActive
                currencyCode
            }
        }
        """
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.post(
            GRAPHQL_ENDPOINT,
            json={"query": query},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "channels" in data["data"]:
                channels = data["data"]["channels"]
                print(f"✅ Channels query successful")
                if channels is not None:
                    print(f"✅ Found {len(channels)} channels")
                else:
                    print("✅ Found 0 channels")
                    channels = []
                
                if channels:
                    print("\n🏪 Available channels:")
                    for channel in channels:
                        status = "Active" if channel["isActive"] else "Inactive"
                        print(f"  - {channel['name']} ({channel['slug']}) - {status} - {channel['currencyCode']}")
                
                return True
            else:
                print(f"❌ Channels query error: {data}")
                return False
        else:
            print(f"❌ Channels query returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Channels query failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🚀 Saleor Cloud Deployment Verification")
    print("=" * 50)
    print(f"Testing URL: {SALEOR_URL}")
    print(f"GraphQL Endpoint: {GRAPHQL_ENDPOINT}")
    print("=" * 50)
    
    tests = [
        ("Basic Connectivity", test_basic_connectivity),
        ("GraphQL Endpoint", test_graphql_endpoint),
        ("Channels Query", test_channels_query),
        ("Products Query", test_products_query),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_func():
            passed += 1
        else:
            print(f"\n⚠️  {test_name} test failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your Saleor deployment is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())