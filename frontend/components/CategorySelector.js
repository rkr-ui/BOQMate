import { useState, useEffect } from 'react';

export default function CategorySelector({ onCategoriesChange }) {
  const [categories, setCategories] = useState({});
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/categories`);
      if (response.ok) {
        const data = await response.json();
        setCategories(data);
      }
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryToggle = (categoryKey) => {
    const newSelected = selectedCategories.includes(categoryKey)
      ? selectedCategories.filter(cat => cat !== categoryKey)
      : [...selectedCategories, categoryKey];
    
    setSelectedCategories(newSelected);
    onCategoriesChange(newSelected);
  };

  const handleSelectAll = () => {
    const allCategories = Object.keys(categories);
    setSelectedCategories(allCategories);
    onCategoriesChange(allCategories);
  };

  const handleClearAll = () => {
    setSelectedCategories([]);
    onCategoriesChange([]);
  };

  if (loading) {
    return (
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-2">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-3 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-6 p-4 bg-gray-50 rounded-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">
          Select Construction Categories
        </h3>
        <div className="space-x-2">
          <button
            onClick={handleSelectAll}
            className="text-sm text-indigo-600 hover:text-indigo-500"
          >
            Select All
          </button>
          <button
            onClick={handleClearAll}
            className="text-sm text-gray-600 hover:text-gray-500"
          >
            Clear All
          </button>
        </div>
      </div>
      
      <p className="text-sm text-gray-600 mb-4">
        Choose specific construction categories to focus your BOQ analysis on. 
        Leave all unchecked for a complete analysis.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {Object.entries(categories).map(([key, category]) => (
          <label
            key={key}
            className={`flex items-center p-3 rounded-lg border cursor-pointer transition-colors ${
              selectedCategories.includes(key)
                ? 'border-indigo-500 bg-indigo-50'
                : 'border-gray-200 bg-white hover:border-gray-300'
            }`}
          >
            <input
              type="checkbox"
              checked={selectedCategories.includes(key)}
              onChange={() => handleCategoryToggle(key)}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <div className="ml-3">
              <div className="text-sm font-medium text-gray-900">
                {category.name}
              </div>
              <div className="text-xs text-gray-500">
                {category.keywords.slice(0, 3).join(', ')}...
              </div>
            </div>
          </label>
        ))}
      </div>

      {selectedCategories.length > 0 && (
        <div className="mt-4 p-3 bg-indigo-50 rounded-lg">
          <div className="text-sm font-medium text-indigo-900 mb-2">
            Selected Categories ({selectedCategories.length}):
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedCategories.map(catKey => (
              <span
                key={catKey}
                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800"
              >
                {categories[catKey]?.name}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
} 