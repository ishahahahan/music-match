"""
MusicMatch API - Test & Verification Script
============================================
Quick test to verify the API is working correctly

Run with: python test_api.py
"""

import requests
import json
import sys
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 5

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_test(name: str, result: bool, message: str = ""):
    """Print test result"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if result else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"  {status} - {name}")
    if message:
        print(f"         {message}")

def print_section(title: str):
    """Print section title"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def test_connectivity() -> bool:
    """Test basic API connectivity"""
    print_section("1. Testing Connectivity")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        result = response.status_code == 200
        print_test("API Server Accessible", result, f"Status: {response.status_code}")
        
        if result:
            data = response.json()
            print_test("API Response Valid", True, f"Database: {data.get('database', 'unknown')}")
        
        return result
    except Exception as e:
        print_test("API Server Accessible", False, str(e))
        return False

def test_health() -> bool:
    """Test health check endpoint"""
    print_section("2. Testing Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        result = response.status_code == 200
        print_test("Health Endpoint", result, f"Status: {response.status_code}")
        
        if result:
            data = response.json()
            db_status = data.get("database", "unknown")
            print_test("Database Status", db_status == "connected", f"Status: {db_status}")
        
        return result
    except Exception as e:
        print_test("Health Endpoint", False, str(e))
        return False

def test_auth_endpoints() -> bool:
    """Test authentication endpoints"""
    print_section("3. Testing Authentication Endpoints")
    
    all_pass = True
    
    # Test login URL endpoint
    try:
        response = requests.get(f"{BASE_URL}/auth/login", timeout=TIMEOUT)
        passed = response.status_code == 200
        all_pass = all_pass and passed
        
        print_test("GET /auth/login", passed, f"Status: {response.status_code}")
        
        if passed:
            data = response.json()
            has_url = "auth_url" in data
            print_test("Auth URL Provided", has_url, "Spotify OAuth URL generated")
            all_pass = all_pass and has_url
    except Exception as e:
        print_test("GET /auth/login", False, str(e))
        all_pass = False
    
    return all_pass

def test_stats_endpoint() -> bool:
    """Test statistics endpoint"""
    print_section("4. Testing Statistics Endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/api/stats", timeout=TIMEOUT)
        result = response.status_code == 200
        print_test("GET /api/stats", result, f"Status: {response.status_code}")
        
        if result:
            data = response.json()
            stats = data.get("data", {})
            print(f"\n  {Colors.BLUE}Database Statistics:{Colors.RESET}")
            print(f"    • Total Users: {stats.get('total_users', 0)}")
            print(f"    • Total Artists: {stats.get('total_artists', 0)}")
            print(f"    • Total Tracks: {stats.get('total_tracks', 0)}")
        
        return result
    except Exception as e:
        print_test("GET /api/stats", False, str(e))
        return False

def test_endpoints_structure() -> bool:
    """Verify API endpoints are properly configured"""
    print_section("5. Verifying API Endpoints Structure")
    
    endpoints_to_test = [
        # Auth
        ("GET", "/auth/login"),
        # System
        ("GET", "/health"),
        ("GET", "/api/stats"),
    ]
    
    all_pass = True
    for method, endpoint in endpoints_to_test:
        try:
            url = f"{BASE_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=TIMEOUT)
            else:
                response = requests.post(url, timeout=TIMEOUT)
            
            # Any non-500 status is OK for structure test
            passed = response.status_code < 500
            all_pass = all_pass and passed
            
            status_text = "OK" if passed else f"ERROR ({response.status_code})"
            print_test(f"{method} {endpoint}", passed, status_text)
        except Exception as e:
            print_test(f"{method} {endpoint}", False, str(e))
            all_pass = False
    
    return all_pass

def test_cors_headers() -> bool:
    """Test CORS headers"""
    print_section("6. Testing CORS Configuration")
    
    try:
        response = requests.options(
            f"{BASE_URL}/",
            headers={"Origin": "http://localhost:3000"},
            timeout=TIMEOUT
        )
        
        has_cors = "access-control-allow-origin" in response.headers
        print_test("CORS Headers Present", has_cors)
        
        if has_cors:
            origin = response.headers.get("access-control-allow-origin", "N/A")
            print_test("CORS Origin", True, f"Allow-Origin: {origin}")
        
        return has_cors
    except Exception as e:
        print_test("CORS Test", False, str(e))
        return False

def test_response_format() -> bool:
    """Test API response format"""
    print_section("7. Testing Response Format")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        data = response.json()
        
        # Check for expected response fields
        has_name = "name" in data
        has_version = "version" in data
        has_status = "status" in data
        
        print_test("Response has 'name'", has_name)
        print_test("Response has 'version'", has_version)
        print_test("Response has 'status'", has_status)
        
        return has_name and has_version and has_status
    except Exception as e:
        print_test("Response Format Test", False, str(e))
        return False

def test_error_handling() -> bool:
    """Test error handling"""
    print_section("8. Testing Error Handling")
    
    # Test 404 response
    try:
        response = requests.get(
            f"{BASE_URL}/api/user/nonexistent-user-id",
            timeout=TIMEOUT
        )
        
        is_error = response.status_code == 404
        print_test("404 Error Response", is_error, f"Status: {response.status_code}")
        
        return is_error
    except Exception as e:
        print_test("Error Handling Test", False, str(e))
        return False

def run_all_tests():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║      MusicMatch API - Test & Verification Suite           ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW}Testing API at: {BASE_URL}{Colors.RESET}\n")
    
    # Run all tests
    tests = [
        ("Connectivity", test_connectivity),
        ("Health Check", test_health),
        ("Authentication", test_auth_endpoints),
        ("Statistics", test_stats_endpoint),
        ("Endpoints", test_endpoints_structure),
        ("CORS", test_cors_headers),
        ("Response Format", test_response_format),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"{Colors.RED}Error running test: {e}{Colors.RESET}")
            results.append((test_name, False))
    
    # Summary
    print_section("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"  {Colors.BOLD}Test Results: {passed}/{total} passed{Colors.RESET}\n")
    
    for test_name, result in results:
        status = f"{Colors.GREEN}✓{Colors.RESET}" if result else f"{Colors.RED}✗{Colors.RESET}"
        print(f"  {status} {test_name}")
    
    # Final status
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All tests passed! API is ready to use.{Colors.RESET}")
        print(f"\n  {Colors.BLUE}Next steps:{Colors.RESET}")
        print(f"  1. Visit interactive API docs: http://localhost:8000/docs")
        print(f"  2. Use Python client: python musicmatch_client.py")
        print(f"  3. Read documentation: See API_DOCUMENTATION.md")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Some tests failed. Check issues above.{Colors.RESET}")
        print(f"\n  {Colors.YELLOW}Troubleshooting:{Colors.RESET}")
        print(f"  1. Is server running? uvicorn backend:app --reload")
        print(f"  2. Check .env file has correct credentials")
        print(f"  3. Verify database connection")
        return 1

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
MusicMatch API Test Script
==========================

Usage:
    python test_api.py              # Run all tests
    python test_api.py --help       # Show this help

Requirements:
    • API server running (uvicorn backend:app --reload)
    • Python requests module installed (pip install requests)

Tests:
    1. Connectivity - Check if API server is accessible
    2. Health Check - Verify health endpoint and database
    3. Authentication - Test auth endpoints
    4. Statistics - Check statistics endpoint
    5. Endpoints - Verify endpoint structure
    6. CORS - Test CORS headers
    7. Response Format - Validate response format
    8. Error Handling - Test error responses

Exit Codes:
    0 - All tests passed
    1 - Some tests failed
        """)
        return 0
    
    try:
        return run_all_tests()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}")
        return 1
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}Unexpected error: {e}{Colors.RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
