#!/usr/bin/env python3

import requests
import json
import sys
import os
from datetime import datetime

class KatyaEximCMSAPITester:
    def __init__(self, base_url="https://283bb3ab-9919-422a-aa7a-cdcf2e6e9bce.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.admin_password = "katyaexim2026"

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        self.log(f"Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}", "PASS")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}", "FAIL")
                self.log(f"Response: {response.text[:200]}", "ERROR")
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })
                return False, {}

        except requests.exceptions.Timeout:
            self.log(f"❌ {name} - Request timeout", "FAIL")
            self.failed_tests.append({"test": name, "error": "Request timeout"})
            return False, {}
        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}", "FAIL")
            self.failed_tests.append({"test": name, "error": str(e)})
            return False, {}

    def test_admin_login_success(self):
        """Test successful admin login"""
        success, response = self.run_test(
            "Admin Login (Success)",
            "POST",
            "api/admin/login",
            200,
            data={"password": self.admin_password}
        )
        if success and 'token' in response:
            self.token = response['token']
            self.log(f"✅ Token obtained: {self.token[:20]}...", "SUCCESS")
            return True
        return False

    def test_admin_login_failure(self):
        """Test admin login with wrong password"""
        success, response = self.run_test(
            "Admin Login (Wrong Password)",
            "POST",
            "api/admin/login",
            401,
            data={"password": "wrongpassword"}
        )
        return success

    def test_token_verification(self):
        """Test token verification"""
        if not self.token:
            self.log("❌ No token available for verification", "FAIL")
            return False
        
        success, response = self.run_test(
            "Token Verification",
            "GET",
            "api/admin/verify",
            200
        )
        return success

    def test_get_content(self):
        """Test getting current content"""
        success, response = self.run_test(
            "Get Content",
            "GET",
            "api/admin/content",
            200
        )
        
        if success and 'content' in response:
            content = response['content']
            # Verify content structure
            required_sections = ['hero', 'about', 'products', 'gallery', 'certificates', 'contact']
            for section in required_sections:
                if section not in content:
                    self.log(f"❌ Missing section: {section}", "FAIL")
                    return False
            
            # Verify products array has 6 items
            if len(content.get('products', [])) != 6:
                self.log(f"❌ Expected 6 products, got {len(content.get('products', []))}", "FAIL")
                return False
                
            # Verify gallery array has 5 items
            if len(content.get('gallery', [])) != 5:
                self.log(f"❌ Expected 5 gallery items, got {len(content.get('gallery', []))}", "FAIL")
                return False
                
            # Verify certificates array has 3 items
            if len(content.get('certificates', [])) != 3:
                self.log(f"❌ Expected 3 certificates, got {len(content.get('certificates', []))}", "FAIL")
                return False
                
            self.log("✅ Content structure validated", "SUCCESS")
            return True
        
        return False

    def test_update_content(self):
        """Test updating content"""
        # First get current content
        success, response = self.run_test(
            "Get Content for Update",
            "GET",
            "api/admin/content",
            200
        )
        
        if not success:
            return False
            
        content = response['content']
        
        # Modify hero eyebrow text
        original_eyebrow = content['hero']['eyebrow']
        test_eyebrow = f"TEST MODIFIED - {datetime.now().strftime('%H:%M:%S')}"
        content['hero']['eyebrow'] = test_eyebrow
        
        # Update content
        success, response = self.run_test(
            "Update Content",
            "POST",
            "api/admin/content",
            200,
            data={"content": content}
        )
        
        if success:
            # Verify the change was saved by getting content again
            success2, response2 = self.run_test(
                "Verify Content Update",
                "GET",
                "api/admin/content",
                200
            )
            
            if success2 and response2['content']['hero']['eyebrow'] == test_eyebrow:
                self.log("✅ Content update verified", "SUCCESS")
                
                # Restore original content
                content['hero']['eyebrow'] = original_eyebrow
                self.run_test(
                    "Restore Original Content",
                    "POST",
                    "api/admin/content",
                    200,
                    data={"content": content}
                )
                return True
            else:
                self.log("❌ Content update not reflected", "FAIL")
                return False
        
        return False

    def test_get_images(self):
        """Test getting image list"""
        success, response = self.run_test(
            "Get Images List",
            "GET",
            "api/admin/images",
            200
        )
        
        if success and 'images' in response:
            images = response['images']
            self.log(f"✅ Found {len(images)} images", "SUCCESS")
            
            # Check if logo.png exists
            logo_found = any(img['name'] == 'logo.png' for img in images)
            if logo_found:
                self.log("✅ Logo.png found in image library", "SUCCESS")
            else:
                self.log("⚠️ Logo.png not found in image library", "WARNING")
            
            return True
        
        return False

    def test_image_upload(self):
        """Test image upload (using a simple test file)"""
        # Create a simple test image file
        test_image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        
        url = f"{self.base_url}/api/admin/upload"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        files = {'image': ('test_image.png', test_image_content, 'image/png')}
        
        self.tests_run += 1
        self.log("Testing Image Upload...")
        
        try:
            response = requests.post(url, files=files, headers=headers, timeout=30)
            
            if response.status_code == 200:
                self.tests_passed += 1
                self.log("✅ Image Upload - Status: 200", "PASS")
                
                response_data = response.json()
                if 'image' in response_data and 'name' in response_data['image']:
                    uploaded_filename = response_data['image']['name']
                    self.log(f"✅ Image uploaded: {uploaded_filename}", "SUCCESS")
                    return True, uploaded_filename
                
            else:
                self.log(f"❌ Image Upload - Expected 200, got {response.status_code}", "FAIL")
                self.log(f"Response: {response.text[:200]}", "ERROR")
                self.failed_tests.append({
                    "test": "Image Upload",
                    "expected": 200,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })
                
        except Exception as e:
            self.log(f"❌ Image Upload - Error: {str(e)}", "FAIL")
            self.failed_tests.append({"test": "Image Upload", "error": str(e)})
            
        return False, None

    def test_image_delete(self, filename):
        """Test image deletion"""
        if not filename:
            self.log("❌ No filename provided for deletion test", "FAIL")
            return False
            
        success, response = self.run_test(
            f"Delete Image ({filename})",
            "DELETE",
            f"api/admin/images/{filename}",
            200
        )
        return success

    def test_contact_form(self):
        """Test contact form submission"""
        success, response = self.run_test(
            "Contact Form Submission",
            "POST",
            "api/contact",
            200,
            data={
                "name": "Test User",
                "email": "test@example.com",
                "message": "This is a test message from the API tester."
            }
        )
        return success

    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log("🚀 Starting KatyaExim CMS API Tests", "START")
        self.log(f"Base URL: {self.base_url}")
        
        # Test 1: Admin Login (Success)
        if not self.test_admin_login_success():
            self.log("❌ Admin login failed - stopping tests", "CRITICAL")
            return self.generate_report()
        
        # Test 2: Admin Login (Failure)
        self.test_admin_login_failure()
        
        # Test 3: Token Verification
        self.test_token_verification()
        
        # Test 4: Get Content
        self.test_get_content()
        
        # Test 5: Update Content
        self.test_update_content()
        
        # Test 6: Get Images
        self.test_get_images()
        
        # Test 7: Image Upload
        upload_success, uploaded_filename = self.test_image_upload()
        
        # Test 8: Image Delete (only if upload succeeded)
        if upload_success and uploaded_filename:
            self.test_image_delete(uploaded_filename)
        
        # Test 9: Contact Form
        self.test_contact_form()
        
        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        self.log("📊 Test Results Summary", "SUMMARY")
        self.log(f"Tests Run: {self.tests_run}")
        self.log(f"Tests Passed: {self.tests_passed}")
        self.log(f"Tests Failed: {len(self.failed_tests)}")
        self.log(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.failed_tests:
            self.log("❌ Failed Tests:", "FAILURES")
            for failure in self.failed_tests:
                error_msg = failure.get('error', f"Expected {failure.get('expected')}, got {failure.get('actual')}")
                self.log(f"  - {failure['test']}: {error_msg}")
        
        return {
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "tests_failed": len(self.failed_tests),
            "success_rate": (self.tests_passed/self.tests_run*100) if self.tests_run > 0 else 0,
            "failed_tests": self.failed_tests,
            "token_obtained": bool(self.token)
        }

def main():
    tester = KatyaEximCMSAPITester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    if results["tests_failed"] == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️ {results['tests_failed']} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())