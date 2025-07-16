import React, { useState, useEffect } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [user, setUser] = useState(null);
  const [categories, setCategories] = useState([]);
  const [income, setIncome] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [currentMonth, setCurrentMonth] = useState(new Date().getMonth() + 1);
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);

  // Mock user for demo
  const mockUser = {
    id: 'user-1',
    name: 'John Doe',
    email: 'john@example.com',
    monthly_budget: 3000
  };

  useEffect(() => {
    setUser(mockUser);
    loadCategories();
    loadData();
  }, []);

  useEffect(() => {
    if (user) {
      loadData();
    }
  }, [currentMonth, currentYear, user]);

  const loadCategories = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/categories`);
      const data = await response.json();
      setCategories(data.categories);
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const loadData = async () => {
    if (!user) return;
    
    setLoading(true);
    try {
      // Load income
      const incomeResponse = await fetch(`${BACKEND_URL}/api/income/${user.id}?month=${currentMonth}&year=${currentYear}`);
      const incomeData = await incomeResponse.json();
      setIncome(incomeData.income || []);

      // Load expenses
      const expenseResponse = await fetch(`${BACKEND_URL}/api/expenses/${user.id}?month=${currentMonth}&year=${currentYear}`);
      const expenseData = await expenseResponse.json();
      setExpenses(expenseData.expenses || []);

      // Load analysis
      const analysisResponse = await fetch(`${BACKEND_URL}/api/analysis/${user.id}?month=${currentMonth}&year=${currentYear}`);
      const analysisData = await analysisResponse.json();
      setAnalysis(analysisData);

      // Load recommendations
      const recommendationResponse = await fetch(`${BACKEND_URL}/api/recommendations/${user.id}?month=${currentMonth}&year=${currentYear}`);
      const recommendationData = await recommendationResponse.json();
      setRecommendations(recommendationData.recommendations || []);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const addIncome = async (incomeData) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/income`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...incomeData,
          user_id: user.id,
          date: new Date().toISOString()
        }),
      });
      
      if (response.ok) {
        loadData();
      }
    } catch (error) {
      console.error('Error adding income:', error);
    }
  };

  const addExpense = async (expenseData) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/expenses`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...expenseData,
          user_id: user.id,
          date: new Date().toISOString()
        }),
      });
      
      if (response.ok) {
        loadData();
      }
    } catch (error) {
      console.error('Error adding expense:', error);
    }
  };

  const deleteExpense = async (expenseId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/expenses/${expenseId}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        loadData();
      }
    } catch (error) {
      console.error('Error deleting expense:', error);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const getMonthName = (month) => {
    const months = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ];
    return months[month - 1];
  };

  const Dashboard = () => (
    <div className="space-y-6">
      {/* Month Navigation */}
      <div className="flex items-center justify-between bg-white p-4 rounded-lg shadow-sm">
        <button
          onClick={() => {
            if (currentMonth === 1) {
              setCurrentMonth(12);
              setCurrentYear(currentYear - 1);
            } else {
              setCurrentMonth(currentMonth - 1);
            }
          }}
          className="text-blue-600 hover:text-blue-800 font-medium"
        >
          ← Previous
        </button>
        <h2 className="text-xl font-bold text-gray-800">
          {getMonthName(currentMonth)} {currentYear}
        </h2>
        <button
          onClick={() => {
            if (currentMonth === 12) {
              setCurrentMonth(1);
              setCurrentYear(currentYear + 1);
            } else {
              setCurrentMonth(currentMonth + 1);
            }
          }}
          className="text-blue-600 hover:text-blue-800 font-medium"
        >
          Next →
        </button>
      </div>

      {/* Overview Cards */}
      {analysis && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h3 className="text-sm font-medium text-gray-500">Total Income</h3>
            <p className="text-2xl font-bold text-green-600">{formatCurrency(analysis.total_income)}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h3 className="text-sm font-medium text-gray-500">Total Expenses</h3>
            <p className="text-2xl font-bold text-red-600">{formatCurrency(analysis.total_expenses)}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h3 className="text-sm font-medium text-gray-500">Remaining Budget</h3>
            <p className={`text-2xl font-bold ${analysis.remaining_budget >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(analysis.remaining_budget)}
            </p>
          </div>
        </div>
      )}

      {/* Spending by Category */}
      {analysis && Object.keys(analysis.category_breakdown).length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Spending by Category</h3>
          <div className="space-y-4">
            {Object.entries(analysis.category_breakdown).map(([category, amount]) => {
              const categoryInfo = categories.find(c => c.name === category);
              return (
                <div key={category} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{categoryInfo?.icon || '📦'}</span>
                    <span className="font-medium text-gray-700">{category}</span>
                  </div>
                  <span className="font-bold text-gray-800">{formatCurrency(amount)}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Overspending Alert */}
      {analysis && analysis.overspending_categories && analysis.overspending_categories.length > 0 && (
        <div className="bg-red-50 border border-red-200 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-red-800 mb-4">⚠️ Overspending Alert</h3>
          <div className="space-y-3">
            {analysis.overspending_categories.map((category, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-red-700 font-medium">{category.category}</span>
                <span className="text-red-600">
                  {formatCurrency(category.overspent)} over budget
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Savings Tips */}
      {recommendations.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-800 mb-4">💡 Savings Tips</h3>
          <div className="space-y-4">
            {recommendations.slice(0, 3).map((rec, index) => (
              <div key={index} className="bg-white p-4 rounded-lg">
                <h4 className="font-medium text-gray-800 mb-2">{rec.category}</h4>
                <p className="text-sm text-gray-600 mb-2">
                  Potential savings: {formatCurrency(rec.potential_savings)}
                </p>
                <ul className="text-sm text-gray-600 space-y-1">
                  {rec.tips.slice(0, 2).map((tip, tipIndex) => (
                    <li key={tipIndex} className="flex items-start">
                      <span className="text-blue-600 mr-2">•</span>
                      {tip}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const IncomeForm = () => {
    const [incomeAmount, setIncomeAmount] = useState('');
    const [incomeSource, setIncomeSource] = useState('');

    const handleSubmit = (e) => {
      e.preventDefault();
      if (incomeAmount && incomeSource) {
        addIncome({
          amount: parseFloat(incomeAmount),
          source: incomeSource,
        });
        setIncomeAmount('');
        setIncomeSource('');
      }
    };

    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-800">Add Income</h2>
        
        <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-sm space-y-4">
          <div>
            <label htmlFor="amount" className="block text-sm font-medium text-gray-700 mb-2">
              Amount
            </label>
            <input
              type="number"
              id="amount"
              step="0.01"
              value={incomeAmount}
              onChange={(e) => setIncomeAmount(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter amount"
              required
            />
          </div>
          
          <div>
            <label htmlFor="source" className="block text-sm font-medium text-gray-700 mb-2">
              Source
            </label>
            <input
              type="text"
              id="source"
              value={incomeSource}
              onChange={(e) => setIncomeSource(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., Salary, Freelance, Investment"
              required
            />
          </div>
          
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
          >
            Add Income
          </button>
        </form>

        {/* Income List */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Income This Month</h3>
          {income.length === 0 ? (
            <p className="text-gray-500">No income recorded this month.</p>
          ) : (
            <div className="space-y-3">
              {income.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                  <div>
                    <p className="font-medium text-gray-800">{item.source}</p>
                    <p className="text-sm text-gray-600">{new Date(item.date).toLocaleDateString()}</p>
                  </div>
                  <p className="font-bold text-green-600">{formatCurrency(item.amount)}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  const ExpenseForm = () => {
    const [expenseAmount, setExpenseAmount] = useState('');
    const [expenseDescription, setExpenseDescription] = useState('');
    const [expenseCategory, setExpenseCategory] = useState('');

    const handleSubmit = (e) => {
      e.preventDefault();
      if (expenseAmount && expenseDescription && expenseCategory) {
        addExpense({
          amount: parseFloat(expenseAmount),
          description: expenseDescription,
          category_id: expenseCategory,
        });
        setExpenseAmount('');
        setExpenseDescription('');
        setExpenseCategory('');
      }
    };

    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-800">Add Expense</h2>
        
        <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-sm space-y-4">
          <div>
            <label htmlFor="expense-amount" className="block text-sm font-medium text-gray-700 mb-2">
              Amount
            </label>
            <input
              type="number"
              id="expense-amount"
              step="0.01"
              value={expenseAmount}
              onChange={(e) => setExpenseAmount(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter amount"
              required
            />
          </div>
          
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <input
              type="text"
              id="description"
              value={expenseDescription}
              onChange={(e) => setExpenseDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., Groceries, Gas, Movie tickets"
              required
            />
          </div>
          
          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              id="category"
              value={expenseCategory}
              onChange={(e) => setExpenseCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              <option value="">Select a category</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.icon} {category.name}
                </option>
              ))}
            </select>
          </div>
          
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
          >
            Add Expense
          </button>
        </form>

        {/* Expense List */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Expenses This Month</h3>
          {expenses.length === 0 ? (
            <p className="text-gray-500">No expenses recorded this month.</p>
          ) : (
            <div className="space-y-3">
              {expenses.map((expense, index) => {
                const category = categories.find(c => c.id === expense.category_id);
                return (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{category?.icon || '📦'}</span>
                      <div>
                        <p className="font-medium text-gray-800">{expense.description}</p>
                        <p className="text-sm text-gray-600">{category?.name || 'Unknown'} • {new Date(expense.date).toLocaleDateString()}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <p className="font-bold text-red-600">{formatCurrency(expense.amount)}</p>
                      <button
                        onClick={() => deleteExpense(expense.id)}
                        className="text-red-500 hover:text-red-700 text-sm"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your financial data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-blue-600">💰 Personal Finance</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">Welcome, {user?.name}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {[
              { id: 'dashboard', label: '📊 Dashboard', icon: '📊' },
              { id: 'income', label: '💰 Income', icon: '💰' },
              { id: 'expenses', label: '💳 Expenses', icon: '💳' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'income' && <IncomeForm />}
        {activeTab === 'expenses' && <ExpenseForm />}
      </main>
    </div>
  );
}

export default App;