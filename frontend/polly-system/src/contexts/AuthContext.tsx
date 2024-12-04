import React, { createContext, useContext, useState, useEffect } from 'react';
import { useLocalStorage } from '@/hooks/use-local-storage';
import api from '@/lib/api';

interface AuthContextType {
  isAuthenticated: boolean;
  user: any | null;
  login: (credentials: { username: string; password: string }) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useLocalStorage<string | null>('auth_token', null);
  const [user, setUser] = useState<any | null>(null);

  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete api.defaults.headers.common['Authorization'];
    }
  }, [token]);

  const login = async (credentials: { username: string; password: string }) => {
    try {
      const response = await api.post('/auth/login', credentials);
      setToken(response.data.token);
      setUser(response.data.user);
    } catch (error) {
      throw new Error('Authentication failed');
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: !!token,
        user,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
