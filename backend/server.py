from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from typing import List, Optional
import pymongo
from pymongo import MongoClient
import os
from datetime import datetime, timedelta
import uuid
from collections import defaultdict
import calendar
from bson import ObjectId
import json
from bson import ObjectId

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URL)
db = client.personal_finance

# Collections
users_collection = db.users
income_collection = db.income
expenses_collection = db.expenses
categories_collection = db.categories

# Helper function to convert ObjectId to string and make documents JSON serializable
def convert_object_id(doc):
    """Convert MongoDB ObjectId to string for JSON serialization"""
    if isinstance(doc, list):
        return [convert_object_id(item) for item in doc]
    elif isinstance(doc, dict):
        return {
            key: str(value) if isinstance(value, ObjectId) else convert_object_id(value)
            for key, value in doc.items()
        }
    elif isinstance(doc, ObjectId):
        return str(doc)
    else:
        return doc

# Custom JSON encoder for ObjectId
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

# Pydantic models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    monthly_budget: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }

class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    color: str
    icon: str
    budget_percentage: float = 0.0
    
    class Config:
        json_encoders = {
            ObjectId: str
        }

class Income(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    amount: float
    source: str
    date: datetime = Field(default_factory=datetime.utcnow)
    month: int
    year: int
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }

class Expense(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    amount: float
    description: str
    category_id: str
    date: datetime = Field(default_factory=datetime.utcnow)
    month: int
    year: int
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }

class SpendingAnalysis(BaseModel):
    total_income: float
    total_expenses: float
    remaining_budget: float
    category_breakdown: dict
    overspending_categories: List[dict]
    savings_rate: float
    month_comparison: dict

class SavingsRecommendation(BaseModel):
    category: str
    current_spending: float
    recommended_budget: float
    potential_savings: float
    tips: List[str]

# Initialize default categories
DEFAULT_CATEGORIES = [
    {"name": "Food & Dining", "color": "#3B82F6", "icon": "🍽️", "budget_percentage": 15},
    {"name": "Transportation", "color": "#10B981", "icon": "🚗", "budget_percentage": 12},
    {"name": "Entertainment", "color": "#F59E0B", "icon": "🎬", "budget_percentage": 8},
    {"name": "Bills & Utilities", "color": "#EF4444", "icon": "⚡", "budget_percentage": 25},
    {"name": "Healthcare", "color": "#8B5CF6", "icon": "🏥", "budget_percentage": 10},
    {"name": "Shopping", "color": "#EC4899", "icon": "🛍️", "budget_percentage": 10},
    {"name": "Housing", "color": "#6B7280", "icon": "🏠", "budget_percentage": 30},
    {"name": "Education", "color": "#14B8A6", "icon": "📚", "budget_percentage": 5},
    {"name": "Other", "color": "#94A3B8", "icon": "📦", "budget_percentage": 5}
]

@app.on_event("startup")
async def startup_event():
    # Initialize categories if they don't exist
    if categories_collection.count_documents({}) == 0:
        for cat_data in DEFAULT_CATEGORIES:
            category = Category(**cat_data)
            categories_collection.insert_one(category.dict())

# Helper functions
def get_monthly_data(user_id: str, month: int, year: int):
    income_data = list(income_collection.find({"user_id": user_id, "month": month, "year": year}))
    expense_data = list(expenses_collection.find({"user_id": user_id, "month": month, "year": year}))
    return income_data, expense_data

def categorize_expenses(expenses: List[dict]) -> dict:
    categories = {cat["id"]: cat for cat in categories_collection.find()}
    breakdown = defaultdict(float)
    
    for expense in expenses:
        category_id = expense.get("category_id")
        if category_id in categories:
            breakdown[categories[category_id]["name"]] += expense["amount"]
    
    return dict(breakdown)

def detect_overspending(user_id: str, month: int, year: int) -> List[dict]:
    _, expenses = get_monthly_data(user_id, month, year)
    category_spending = categorize_expenses(expenses)
    
    # Get user's monthly budget
    user = users_collection.find_one({"id": user_id})
    if not user:
        return []
    
    monthly_budget = user.get("monthly_budget", 0)
    if monthly_budget == 0:
        return []
    
    categories = {cat["name"]: cat for cat in categories_collection.find()}
    overspending = []
    
    for category_name, spent in category_spending.items():
        if category_name in categories:
            expected_budget = monthly_budget * (categories[category_name]["budget_percentage"] / 100)
            if spent > expected_budget:
                overspending.append({
                    "category": category_name,
                    "spent": spent,
                    "budget": expected_budget,
                    "overspent": spent - expected_budget,
                    "percentage": ((spent - expected_budget) / expected_budget) * 100
                })
    
    return sorted(overspending, key=lambda x: x["overspent"], reverse=True)

def generate_savings_tips(overspending_data: List[dict]) -> List[SavingsRecommendation]:
    tips_db = {
        "Food & Dining": [
            "Cook more meals at home instead of ordering takeout",
            "Plan weekly meals and create shopping lists",
            "Use grocery store apps for discounts and coupons",
            "Buy generic brands instead of name brands"
        ],
        "Transportation": [
            "Use public transportation when possible",
            "Combine errands into single trips",
            "Consider carpooling or ridesharing",
            "Walk or bike for short distances"
        ],
        "Entertainment": [
            "Look for free community events and activities",
            "Use streaming services instead of cable TV",
            "Take advantage of happy hour specials",
            "Host gatherings at home instead of going out"
        ],
        "Shopping": [
            "Wait 24 hours before making non-essential purchases",
            "Compare prices across different stores",
            "Buy items during sales and clearance events",
            "Use cashback apps and reward programs"
        ],
        "Bills & Utilities": [
            "Review and negotiate your monthly subscriptions",
            "Switch to energy-efficient appliances",
            "Use programmable thermostats",
            "Bundle services for better rates"
        ]
    }
    
    recommendations = []
    for category_data in overspending_data:
        category = category_data["category"]
        current_spending = category_data["spent"]
        recommended_budget = category_data["budget"]
        potential_savings = category_data["overspent"]
        
        tips = tips_db.get(category, ["Review your spending in this category"])
        
        recommendations.append(SavingsRecommendation(
            category=category,
            current_spending=current_spending,
            recommended_budget=recommended_budget,
            potential_savings=potential_savings,
            tips=tips
        ))
    
    return recommendations

# API Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/categories")
async def get_categories():
    categories = list(categories_collection.find({}, {"_id": 0}))
    return {"categories": categories}

@app.post("/api/users")
async def create_user(user: User):
    # Check if user already exists
    existing_user = users_collection.find_one({"email": user.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user_dict = user.dict()
    users_collection.insert_one(user_dict)
    
    # Return user data without MongoDB ObjectId
    return {"message": "User created successfully", "user": jsonable_encoder(user_dict)}

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    user = users_collection.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return jsonable_encoder(user)

@app.put("/api/users/{user_id}")
async def update_user(user_id: str, user_update: dict):
    result = users_collection.update_one(
        {"id": user_id},
        {"$set": user_update}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User updated successfully"}

@app.post("/api/income")
async def add_income(income: Income):
    # Set month and year from date
    income.month = income.date.month
    income.year = income.date.year
    
    income_dict = income.dict()
    income_collection.insert_one(income_dict)
    return {"message": "Income added successfully", "income": jsonable_encoder(income_dict)}

@app.get("/api/income/{user_id}")
async def get_income(user_id: str, month: int = None, year: int = None):
    query = {"user_id": user_id}
    if month and year:
        query.update({"month": month, "year": year})
    
    income_data = list(income_collection.find(query, {"_id": 0}))
    return {"income": jsonable_encoder(income_data)}

@app.post("/api/expenses")
async def add_expense(expense: Expense):
    # Set month and year from date
    expense.month = expense.date.month
    expense.year = expense.date.year
    
    expense_dict = expense.dict()
    expenses_collection.insert_one(expense_dict)
    return {"message": "Expense added successfully", "expense": jsonable_encoder(expense_dict)}

@app.get("/api/expenses/{user_id}")
async def get_expenses(user_id: str, month: int = None, year: int = None):
    query = {"user_id": user_id}
    if month and year:
        query.update({"month": month, "year": year})
    
    expense_data = list(expenses_collection.find(query, {"_id": 0}))
    return {"expenses": jsonable_encoder(expense_data)}

@app.delete("/api/expenses/{expense_id}")
async def delete_expense(expense_id: str):
    result = expenses_collection.delete_one({"id": expense_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": "Expense deleted successfully"}

@app.get("/api/analysis/{user_id}")
async def get_spending_analysis(user_id: str, month: int = None, year: int = None):
    if not month or not year:
        now = datetime.utcnow()
        month = now.month
        year = now.year
    
    income_data, expense_data = get_monthly_data(user_id, month, year)
    
    total_income = sum(income["amount"] for income in income_data)
    total_expenses = sum(expense["amount"] for expense in expense_data)
    remaining_budget = total_income - total_expenses
    
    category_breakdown = categorize_expenses(expense_data)
    overspending_categories = detect_overspending(user_id, month, year)
    
    savings_rate = (remaining_budget / total_income * 100) if total_income > 0 else 0
    
    # Get previous month for comparison
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    
    prev_income_data, prev_expense_data = get_monthly_data(user_id, prev_month, prev_year)
    prev_total_expenses = sum(expense["amount"] for expense in prev_expense_data)
    
    month_comparison = {
        "current_month": total_expenses,
        "previous_month": prev_total_expenses,
        "difference": total_expenses - prev_total_expenses,
        "percentage_change": ((total_expenses - prev_total_expenses) / prev_total_expenses * 100) if prev_total_expenses > 0 else 0
    }
    
    analysis = SpendingAnalysis(
        total_income=total_income,
        total_expenses=total_expenses,
        remaining_budget=remaining_budget,
        category_breakdown=category_breakdown,
        overspending_categories=overspending_categories,
        savings_rate=savings_rate,
        month_comparison=month_comparison
    )
    
    return jsonable_encoder(analysis.dict())

@app.get("/api/recommendations/{user_id}")
async def get_savings_recommendations(user_id: str, month: int = None, year: int = None):
    if not month or not year:
        now = datetime.utcnow()
        month = now.month
        year = now.year
    
    overspending_data = detect_overspending(user_id, month, year)
    recommendations = generate_savings_tips(overspending_data)
    
    return {"recommendations": jsonable_encoder([rec.dict() for rec in recommendations])}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)