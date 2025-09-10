// Authentication API module

import axios from 'axios';
import type { NewsTask, NewsTaskCreate, CryptoTask, CryptoTaskCreate, Event } from './interface';


const API_BASE_URL = '/api';
// FOR LOCAL DEBUG
// const API_BASE_URL = 'http://localhost:8030/api';

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
  async logout(): Promise<void> {
      try {
        await api.post('/auth/jwt/logout');
      } catch (error) {
        console.error('Logout failed:', error);
      } finally {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        window.dispatchEvent(new Event('auth-logout'));
      }
  },

  // Check if user is authenticated
  async isAuthenticated(): Promise<boolean> {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
      return false;
    }

    try {
      await api.get('/users/me');
      return true;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        localStorage.removeItem(TOKEN_STORAGE_KEY); // Clean up invalid token
      }
      return false;
    }
  },
  getToken(): string | null {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  },
  removeToken(): void {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
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

export const cryptoTaskApi = {
  // Get all crypto tasks for current user
  async getTasks(): Promise<CryptoTask[]> {
    try {
      const response = await api.get('/crypto_task/');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch crypto tasks:', error);
      return [];
    }
  },
  
  // Get a specific crypto task by ID
  async getTask(taskId: number): Promise<CryptoTask | null> {
    try {
      const response = await api.get(`/crypto_task/${taskId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch crypto task ${taskId}:`, error);
      return null;
    }
  },
  
  // Create a new crypto task
  async createTask(data: CryptoTaskCreate): Promise<CryptoTask | null> {
    try {
      const response = await api.post<CryptoTask>('/crypto_task/', data);
      return response.data;
    } catch (error) {
      console.error('Failed to create crypto task:', error);
      return null;
    }
  },
  
  // Delete crypto task by ID
  async deleteTask(taskId: number): Promise<boolean> {
    try {
      await api.delete(`/crypto_task/${taskId}`);
      return true;
    } catch (error) {
      console.error(`Failed to delete crypto task ${taskId}:`, error);
      return false;
    }
  },

  // Update an existing crypto task
  async updateTask(taskId: number, data: CryptoTask): Promise<CryptoTask | null> {
    try {
      const response = await api.put<CryptoTask>(`/crypto_task/${taskId}`, data);
      return response.data;
    }
    catch (error) {
      console.error(`Failed to update crypto task ${taskId}:`, error);
      return null;
    }
  },
};


export class CrudApi<T, TCreate = Partial<T>, TUpdate = Partial<T>> {
  private endpoint: string;
  
  constructor(endpoint: string) {
    this.endpoint = endpoint;
  }

  // Get all items
  async getAll(): Promise<T[]> {
    try {
      const response = await api.get<T[]>(`/${this.endpoint}/`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch ${this.endpoint}:`, error);
      return [];
    }
  }

  // Get item by ID
  async getById(id: number | string): Promise<T | null> {
    try {
      const response = await api.get<T>(`/${this.endpoint}/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch ${this.endpoint} ${id}:`, error);
      return null;
    }
  }

  // Create new item
  async create(data: TCreate): Promise<T | null> {
    try {
      const response = await api.post<T>(`/${this.endpoint}/`, data);
      return response.data;
    } catch (error) {
      console.error(`Failed to create ${this.endpoint}:`, error);
      return null;
    }
  }

  // Update existing item
  async update(id: number | string, data: TUpdate): Promise<T | null> {
    try {
      const response = await api.put<T>(`/${this.endpoint}/${id}`, data);
      return response.data;
    } catch (error) {
      console.error(`Failed to update ${this.endpoint} ${id}:`, error);
      return null;
    }
  }

  // Delete item
  async delete(id: number | string): Promise<boolean> {
    try {
      await api.delete(`/${this.endpoint}/${id}`);
      return true;
    } catch (error) {
      console.error(`Failed to delete ${this.endpoint} ${id}:`, error);
      return false;
    }
  }

  // Patch item (partial update)
  async patch(id: number | string, data: Partial<TUpdate>): Promise<T | null> {
    try {
      const response = await api.patch<T>(`/${this.endpoint}/${id}`, data);
      return response.data;
    } catch (error) {
      console.error(`Failed to patch ${this.endpoint} ${id}:`, error);
      return null;
    }
  }

  // Custom endpoint call
  async customCall<TResponse = any>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
    path: string,
    data?: any
  ): Promise<TResponse | null> {
    try {
      const response = await api.request<TResponse>({
        method: method.toLowerCase() as any,
        url: `/${this.endpoint}/${path}`,
        data,
      });
      return response.data;
    } catch (error) {
      console.error(`Failed to call ${method} /${this.endpoint}/${path}:`, error);
      return null;
    }
  }
}

export const eventsAPI = new CrudApi<Event>('events');
