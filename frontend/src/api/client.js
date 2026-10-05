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

// Auth / user profile
export const getMe = async () => {
  const { data } = await api.get('/me');
  return data;
};

export const registerUser = async ({ username, displayName, password, inviteToken }) => {
  const { data } = await api.post('/register', {
    username,
    display_name: displayName,
    password,
    ...(inviteToken ? { invite_token: inviteToken } : {}),
  });
  return data;
};

export const unlinkTelegram = async () => {
  const { data } = await api.patch('/me/telegram', { telegram_id: null });
  return data;
};

export const changePassword = async ({ currentPassword, newPassword }) => {
  // Self-service password change: uses the member's own PATCH endpoint
  const me = await getMe();
  const { data } = await api.patch(`/members/${me.id}/password`, { password: newPassword });
  return data;
};

// Member management (admin only)
export const getMembers = async () => {
  const { data } = await api.get('/members');
  return data;
};

export const addMember = async ({ username, displayName, password, role = 'member' }) => {
  const { data } = await api.post('/members', { username, display_name: displayName, password, role });
  return data;
};

export const deleteMember = async (id) => {
  const { data } = await api.delete(`/members/${id}`);
  return data;
};

export const resetMemberPassword = async (id, password) => {
  const { data } = await api.patch(`/members/${id}/password`, { password });
  return data;
};

// Phone-number invites (admin generates a link, shares it themselves via Telegram)
export const getMemberInvites = async () => {
  const { data } = await api.get('/members/invites');
  return data;
};

export const createMemberInvite = async ({ phoneNumber, displayName }) => {
  const { data } = await api.post('/members/invite', { phone_number: phoneNumber, display_name: displayName });
  return data;
};

export const cancelMemberInvite = async (id) => {
  const { data } = await api.delete(`/members/invites/${id}`);
  return data;
};

export const getInvitePreview = async (token) => {
  const { data } = await api.get(`/invites/${token}`);
  return data;
};

// Insight agent (chat Q&A + on-demand monthly narrative)
export const askInsightAgent = async (question, history = []) => {
  const { data } = await api.post('/insights/ask', { question, history });
  return data.answer;
};

export const generateMonthlyInsight = async () => {
  const { data } = await api.post('/insights/generate');
  return data.insight;
};

export const csvExportUrl = '/api/export/csv';

export default api;
