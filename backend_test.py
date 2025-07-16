#!/usr/bin/env python3
"""
Backend API Testing for Personal Finance App
Tests all backend endpoints with realistic data
"""

import requests
import json
from datetime import datetime, timedelta
import uuid
import sys

# Get backend URL from environment
BACKEND_URL = "https://a347688f-a8df-482e-89ae-b6e2deaa12b8.preview.emergentagent.com/api"

class PersonalFinanceAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_user_id = None
        self.test_categories = []
        self.test_income_ids = []
        self.test_expense_ids = []
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }

    def log_result(self, test_name, success, message=""):
        if success:
            self.results["passed"] += 1
            print(f"✅ {test_name}: PASSED {message}")
        else:
            self.results["failed"] += 1
            self.results["errors"].append(f"{test_name}: {message}")
            print(f"❌ {test_name}: FAILED - {message}")

    def test_health_check(self):
        """Test the health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_result("Health Check", True)
                    return True
                else:
                    self.log_result("Health Check", False, f"Unexpected response: {data}")
            else:
                self.log_result("Health Check", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("Health Check", False, f"Exception: {str(e)}")
        return False

    def test_get_categories(self):
        """Test getting expense categories"""
        try:
            response = requests.get(f"{self.base_url}/categories")
            if response.status_code == 200:
                data = response.json()
                if "categories" in data and len(data["categories"]) > 0:
                    self.test_categories = data["categories"]
                    # Verify category structure
                    first_category = data["categories"][0]
                    required_fields = ["id", "name", "color", "icon", "budget_percentage"]
                    if all(field in first_category for field in required_fields):
                        self.log_result("Get Categories", True, f"Found {len(data['categories'])} categories")
                        return True
                    else:
                        self.log_result("Get Categories", False, "Missing required fields in category")
                else:
                    self.log_result("Get Categories", False, "No categories returned")
            else:
                self.log_result("Get Categories", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("Get Categories", False, f"Exception: {str(e)}")
        return False

    def test_create_user(self):
        """Test creating a new user"""
        try:
            user_data = {
                "name": "Sarah Johnson",
                "email": f"sarah.johnson.{uuid.uuid4().hex[:8]}@example.com",
                "monthly_budget": 3000.0
            }
            
            response = requests.post(f"{self.base_url}/users", json=user_data)
            if response.status_code == 200:
                data = response.json()
                if "user" in data and "id" in data["user"]:
                    self.test_user_id = data["user"]["id"]
                    self.log_result("Create User", True, f"User ID: {self.test_user_id}")
                    return True
                else:
                    self.log_result("Create User", False, "No user ID in response")
            else:
                self.log_result("Create User", False, f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Create User", False, f"Exception: {str(e)}")
        return False

    def test_get_user(self):
        """Test getting user details"""
        if not self.test_user_id:
            self.log_result("Get User", False, "No test user ID available")
            return False
            
        try:
            response = requests.get(f"{self.base_url}/users/{self.test_user_id}")
            if response.status_code == 200:
                data = response.json()
                if data.get("id") == self.test_user_id and "name" in data:
                    self.log_result("Get User", True, f"Retrieved user: {data.get('name')}")
                    return True
                else:
                    self.log_result("Get User", False, "Invalid user data returned")
            else:
                self.log_result("Get User", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("Get User", False, f"Exception: {str(e)}")
        return False

    def test_update_user(self):
        """Test updating user information"""
        if not self.test_user_id:
            self.log_result("Update User", False, "No test user ID available")
            return False
            
        try:
            update_data = {
                "monthly_budget": 3500.0,
                "name": "Sarah Johnson-Smith"
            }
            
            response = requests.put(f"{self.base_url}/users/{self.test_user_id}", json=update_data)
            if response.status_code == 200:
                # Verify the update by getting the user
                get_response = requests.get(f"{self.base_url}/users/{self.test_user_id}")
                if get_response.status_code == 200:
                    user_data = get_response.json()
                    if user_data.get("monthly_budget") == 3500.0:
                        self.log_result("Update User", True, "Budget updated successfully")
                        return True
                    else:
                        self.log_result("Update User", False, "Budget not updated correctly")
                else:
                    self.log_result("Update User", False, "Could not verify update")
            else:
                self.log_result("Update User", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("Update User", False, f"Exception: {str(e)}")
        return False

    def test_add_income(self):
        """Test adding income entries"""
        if not self.test_user_id:
            self.log_result("Add Income", False, "No test user ID available")
            return False
            
        try:
            # Add multiple income entries for different months
            income_entries = [
                {
                    "user_id": self.test_user_id,
                    "amount": 4500.0,
                    "source": "Software Engineer Salary",
                    "date": datetime.now().isoformat()
                },
                {
                    "user_id": self.test_user_id,
                    "amount": 800.0,
                    "source": "Freelance Project",
                    "date": datetime.now().isoformat()
                },
                {
                    "user_id": self.test_user_id,
                    "amount": 4200.0,
                    "source": "Software Engineer Salary",
                    "date": (datetime.now() - timedelta(days=32)).isoformat()
                }
            ]
            
            success_count = 0
            for income in income_entries:
                response = requests.post(f"{self.base_url}/income", json=income)
                if response.status_code == 200:
                    data = response.json()
                    if "income" in data and "id" in data["income"]:
                        self.test_income_ids.append(data["income"]["id"])
                        success_count += 1
                        
            if success_count == len(income_entries):
                self.log_result("Add Income", True, f"Added {success_count} income entries")
                return True
            else:
                self.log_result("Add Income", False, f"Only {success_count}/{len(income_entries)} entries added")
        except Exception as e:
            self.log_result("Add Income", False, f"Exception: {str(e)}")
        return False

    def test_get_income(self):
        """Test getting income data with and without filtering"""
        if not self.test_user_id:
            self.log_result("Get Income", False, "No test user ID available")
            return False
            
        try:
            # Test getting all income
            response = requests.get(f"{self.base_url}/income/{self.test_user_id}")
            if response.status_code == 200:
                data = response.json()
                if "income" in data and len(data["income"]) > 0:
                    all_income_count = len(data["income"])
                    
                    # Test filtering by current month
                    now = datetime.now()
                    filtered_response = requests.get(
                        f"{self.base_url}/income/{self.test_user_id}?month={now.month}&year={now.year}"
                    )
                    
                    if filtered_response.status_code == 200:
                        filtered_data = filtered_response.json()
                        filtered_count = len(filtered_data["income"])
                        
                        self.log_result("Get Income", True, 
                                      f"All: {all_income_count}, Current month: {filtered_count}")
                        return True
                    else:
                        self.log_result("Get Income", False, "Filtering failed")
                else:
                    self.log_result("Get Income", False, "No income data returned")
            else:
                self.log_result("Get Income", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("Get Income", False, f"Exception: {str(e)}")
        return False

    def test_add_expenses(self):
        """Test adding expense entries"""
        if not self.test_user_id or not self.test_categories:
            self.log_result("Add Expenses", False, "Missing user ID or categories")
            return False
            
        try:
            # Create realistic expenses across different categories
            expenses = [
                {
                    "user_id": self.test_user_id,
                    "amount": 450.0,
                    "description": "Weekly groceries at Whole Foods",
                    "category_id": next((c["id"] for c in self.test_categories if c["name"] == "Food & Dining"), self.test_categories[0]["id"]),
                    "date": datetime.now().isoformat()
                },
                {
                    "user_id": self.test_user_id,
                    "amount": 1200.0,
                    "description": "Monthly rent payment",
                    "category_id": next((c["id"] for c in self.test_categories if c["name"] == "Housing"), self.test_categories[0]["id"]),
                    "date": datetime.now().isoformat()
                },
                {
                    "user_id": self.test_user_id,
                    "amount": 85.0,
                    "description": "Gas station fill-up",
                    "category_id": next((c["id"] for c in self.test_categories if c["name"] == "Transportation"), self.test_categories[0]["id"]),
                    "date": datetime.now().isoformat()
                },
                {
                    "user_id": self.test_user_id,
                    "amount": 150.0,
                    "description": "Electricity bill",
                    "category_id": next((c["id"] for c in self.test_categories if c["name"] == "Bills & Utilities"), self.test_categories[0]["id"]),
                    "date": datetime.now().isoformat()
                },
                {
                    "user_id": self.test_user_id,
                    "amount": 75.0,
                    "description": "Movie night with friends",
                    "category_id": next((c["id"] for c in self.test_categories if c["name"] == "Entertainment"), self.test_categories[0]["id"]),
                    "date": datetime.now().isoformat()
                }
            ]
            
            success_count = 0
            for expense in expenses:
                response = requests.post(f"{self.base_url}/expenses", json=expense)
                if response.status_code == 200:
                    data = response.json()
                    if "expense" in data and "id" in data["expense"]:
                        self.test_expense_ids.append(data["expense"]["id"])
                        success_count += 1
                        
            if success_count == len(expenses):
                self.log_result("Add Expenses", True, f"Added {success_count} expense entries")
                return True
            else:
                self.log_result("Add Expenses", False, f"Only {success_count}/{len(expenses)} entries added")
        except Exception as e:
            self.log_result("Add Expenses", False, f"Exception: {str(e)}")
        return False

    def test_get_expenses(self):
        """Test getting expense data with and without filtering"""
        if not self.test_user_id:
            self.log_result("Get Expenses", False, "No test user ID available")
            return False
            
        try:
            # Test getting all expenses
            response = requests.get(f"{self.base_url}/expenses/{self.test_user_id}")
            if response.status_code == 200:
                data = response.json()
                if "expenses" in data and len(data["expenses"]) > 0:
                    all_expenses_count = len(data["expenses"])
                    
                    # Test filtering by current month
                    now = datetime.now()
                    filtered_response = requests.get(
                        f"{self.base_url}/expenses/{self.test_user_id}?month={now.month}&year={now.year}"
                    )
                    
                    if filtered_response.status_code == 200:
                        filtered_data = filtered_response.json()
                        filtered_count = len(filtered_data["expenses"])
                        
                        self.log_result("Get Expenses", True, 
                                      f"All: {all_expenses_count}, Current month: {filtered_count}")
                        return True
                    else:
                        self.log_result("Get Expenses", False, "Filtering failed")
                else:
                    self.log_result("Get Expenses", False, "No expense data returned")
            else:
                self.log_result("Get Expenses", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("Get Expenses", False, f"Exception: {str(e)}")
        return False

    def test_delete_expense(self):
        """Test deleting an expense"""
        if not self.test_expense_ids:
            self.log_result("Delete Expense", False, "No test expense IDs available")
            return False
            
        try:
            expense_id_to_delete = self.test_expense_ids[0]
            response = requests.delete(f"{self.base_url}/expenses/{expense_id_to_delete}")
            
            if response.status_code == 200:
                # Verify deletion by trying to get expenses again
                get_response = requests.get(f"{self.base_url}/expenses/{self.test_user_id}")
                if get_response.status_code == 200:
                    data = get_response.json()
                    remaining_expenses = data.get("expenses", [])
                    if not any(exp["id"] == expense_id_to_delete for exp in remaining_expenses):
                        self.log_result("Delete Expense", True, f"Deleted expense {expense_id_to_delete}")
                        return True
                    else:
                        self.log_result("Delete Expense", False, "Expense still exists after deletion")
                else:
                    self.log_result("Delete Expense", False, "Could not verify deletion")
            else:
                self.log_result("Delete Expense", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("Delete Expense", False, f"Exception: {str(e)}")
        return False

    def test_spending_analysis(self):
        """Test the spending analysis endpoint"""
        if not self.test_user_id:
            self.log_result("Spending Analysis", False, "No test user ID available")
            return False
            
        try:
            now = datetime.now()
            response = requests.get(
                f"{self.base_url}/analysis/{self.test_user_id}?month={now.month}&year={now.year}"
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = [
                    "total_income", "total_expenses", "remaining_budget",
                    "category_breakdown", "overspending_categories", 
                    "savings_rate", "month_comparison"
                ]
                
                if all(field in data for field in required_fields):
                    # Verify calculations make sense
                    total_income = data["total_income"]
                    total_expenses = data["total_expenses"]
                    remaining_budget = data["remaining_budget"]
                    
                    if abs((total_income - total_expenses) - remaining_budget) < 0.01:
                        self.log_result("Spending Analysis", True, 
                                      f"Income: ${total_income}, Expenses: ${total_expenses}, Remaining: ${remaining_budget}")
                        return True
                    else:
                        self.log_result("Spending Analysis", False, "Budget calculation incorrect")
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("Spending Analysis", False, f"Missing fields: {missing_fields}")
            else:
                self.log_result("Spending Analysis", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("Spending Analysis", False, f"Exception: {str(e)}")
        return False

    def test_savings_recommendations(self):
        """Test the savings recommendations endpoint"""
        if not self.test_user_id:
            self.log_result("Savings Recommendations", False, "No test user ID available")
            return False
            
        try:
            now = datetime.now()
            response = requests.get(
                f"{self.base_url}/recommendations/{self.test_user_id}?month={now.month}&year={now.year}"
            )
            
            if response.status_code == 200:
                data = response.json()
                if "recommendations" in data:
                    recommendations = data["recommendations"]
                    
                    # Check if recommendations have proper structure
                    if len(recommendations) > 0:
                        first_rec = recommendations[0]
                        required_fields = ["category", "current_spending", "recommended_budget", "potential_savings", "tips"]
                        
                        if all(field in first_rec for field in required_fields):
                            self.log_result("Savings Recommendations", True, 
                                          f"Generated {len(recommendations)} recommendations")
                            return True
                        else:
                            self.log_result("Savings Recommendations", False, "Invalid recommendation structure")
                    else:
                        self.log_result("Savings Recommendations", True, "No overspending detected - no recommendations needed")
                        return True
                else:
                    self.log_result("Savings Recommendations", False, "No recommendations field in response")
            else:
                self.log_result("Savings Recommendations", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_result("Savings Recommendations", False, f"Exception: {str(e)}")
        return False

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting Personal Finance App Backend API Tests")
        print(f"🔗 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test sequence - order matters for data dependencies
        test_methods = [
            self.test_health_check,
            self.test_get_categories,
            self.test_create_user,
            self.test_get_user,
            self.test_update_user,
            self.test_add_income,
            self.test_get_income,
            self.test_add_expenses,
            self.test_get_expenses,
            self.test_delete_expense,
            self.test_spending_analysis,
            self.test_savings_recommendations
        ]
        
        for test_method in test_methods:
            test_method()
            print()  # Add spacing between tests
        
        # Print final results
        print("=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📈 Success Rate: {(self.results['passed'] / (self.results['passed'] + self.results['failed']) * 100):.1f}%")
        
        if self.results['errors']:
            print("\n🔍 FAILED TESTS:")
            for error in self.results['errors']:
                print(f"  • {error}")
        
        return self.results['failed'] == 0

if __name__ == "__main__":
    tester = PersonalFinanceAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)