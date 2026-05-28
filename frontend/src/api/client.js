import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 20000,
});

// Restore key from localStorage on page load
const storedKey = localStorage.getItem('api_key');
if (storedKey) {
  api.defaults.headers.common['X-Api-Key'] = storedKey;
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

export const csvExportUrl = '/api/export/csv';

export default api;
