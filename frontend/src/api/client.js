import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 20000,
});

// Restore JWT from localStorage on page load
const storedToken = localStorage.getItem('jwt_token');
if (storedToken) {
  api.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
}

export const fetchTransactions = async (month) => {
  const { data } = await api.get('/transactions', { params: month ? { month } : {} });
  return data.transactions || [];
};

export const fetchSummary = async () => {
  const { data } = await api.get('/summary');
  return data;
};

export const fetchCategories = async () => {
  const { data } = await api.get('/categories');
  return data;
};

export const getUsers = async () => {
  const { data } = await api.get('/users');
  return data;
};

export const getTransactionsByUser = async (loggedById) => {
  const { data } = await api.get(`/transactions/user/${loggedById}`);
  return data.transactions || [];
};

export const addTransaction = async (payload) => {
  const { data } = await api.post('/transactions', payload);
  return data;
};

export const deleteTransaction = async (id) => {
  const { data } = await api.delete(`/transactions/${id}`);
  return data;
};

export const cleanGarbage = async () => {
  const { data } = await api.delete('/transactions/clean');
  return data;
};

export const updateTransaction = async (id, fields) => {
  const { data } = await api.patch(`/transactions/${id}`, fields);
  return data;
};

export const bulkUpdateTransactions = async (ids, fields) => {
  const { data } = await api.patch('/transactions/batch', { ids, fields });
  return data;
};

export const fetchCategoriesFull = async () => {
  const { data } = await api.get('/categories/full');
  return data;
};

export const addCategory = async (payload) => {
  const { data } = await api.post('/categories', payload);
  return data;
};

export const addSubcategory = async (categoryName, subcategoryName) => {
  const { data } = await api.post(`/categories/${encodeURIComponent(categoryName)}/subcategories`, { name: subcategoryName });
  return data;
};

export const deleteCategory = async (categoryName) => {
  const { data } = await api.delete(`/categories/${encodeURIComponent(categoryName)}`);
  return data;
};

export const deleteSubcategory = async (categoryName, subcategoryName) => {
  const { data } = await api.delete(`/categories/${encodeURIComponent(categoryName)}/subcategories/${encodeURIComponent(subcategoryName)}`);
  return data;
};

export const csvExportUrl = '/api/export/csv';

export default api;
