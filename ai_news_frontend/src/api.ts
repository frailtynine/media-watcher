// Authentication API module

import axios from 'axios';
import type { NewsTask, NewsTaskCreate } from './interface';


const API_BASE_URL = 'http://localhost:8000/api';
const TOKEN_STORAGE_KEY = 'auth_token';

export interface ApiUser {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

// Create axios instance with some default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor for protected requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authApi = {
  // Login user
  async login(credentials: LoginCredentials): Promise<boolean> {
    try {
      // FastAPI uses form data for login
      const formData = new FormData();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);
      
      const response = await axios.post<LoginResponse>(
        `${API_BASE_URL}/auth/jwt/login`, 
        formData,
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );
      
      const { access_token } = response.data;
      localStorage.setItem(TOKEN_STORAGE_KEY, access_token);
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  },

  // Register new user
  async register(data: RegisterData): Promise<ApiUser | null> {
    try {
      const response = await api.post<ApiUser>('/auth/register', data);
      return response.data;
    } catch (error) {
      console.error('Registration failed:', error);
      return null;
    }
  },

  // Get current user details
  async getCurrentUser(): Promise<ApiUser | null> {
    try {
      const response = await api.get<ApiUser>('/users/me');
      return response.data;
    } catch (error) {
      console.error('Failed to get user:', error);
      return null;
    }
  },

  // Request password reset
  async requestPasswordReset(email: string): Promise<boolean> {
    try {
      await api.post('/auth/forgot-password', { email });
      return true;
    } catch (error) {
      console.error('Password reset request failed:', error);
      return false;
    }
  },

  // Reset password with token
  async resetPassword(token: string, password: string): Promise<boolean> {
    try {
      await api.post('/auth/reset-password', { token, password });
      return true;
    } catch (error) {
      console.error('Password reset failed:', error);
      return false;
    }
  },

  // Logout user
  logout(): void {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  },

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return localStorage.getItem(TOKEN_STORAGE_KEY) !== null;
  },
  getToken(): string | null {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  }
};

export const newsTaskApi = {
  // Get all tasks for current user
  async getTasks(): Promise<NewsTask[]> {
    try {
      const response = await api.get('/news_task/');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
      return [];
    }
  },
  // Get a specific task by ID
  async getTask(taskId: number): Promise<NewsTask | null> {
    try {
      const response = await api.get(`/news_task/${taskId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch task ${taskId}:`, error);
      return null;
    }
  },
  // Create a new task
  async createTask(data: NewsTaskCreate): Promise<NewsTask | null> {
    try {
      const response = await api.post<NewsTask>('/news_task/', data);
      return response.data;
    } catch (error) {
      console.error('Failed to create task:', error);
      return null;
    }
  },
  // Delete task by ID
  async deleteTask(taskId: number): Promise<boolean> {
    try {
      await api.delete(`/news_task/${taskId}`);
      return true;
    } catch (error) {
      console.error(`Failed to delete task ${taskId}:`, error);
      return false;
    }
  },

  // Update an existing task
  async updateTask(taskId: number, data: NewsTask): Promise<NewsTask | null> {
    try {
      const response = await api.put<NewsTask>(`/news_task/${taskId}`, data);
      return response.data;
    }
    catch (error) {
      console.error(`Failed to update task ${taskId}:`, error);
      return null;
    }
  },

};
