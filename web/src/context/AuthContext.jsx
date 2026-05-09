import { createContext, useContext, useState, useEffect } from 'react';
import * as authAPI from '../api/authApi';
import { setAuthToken } from '../api/httpClient';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = sessionStorage.getItem('auth_token');
    if (token) {
      setAuthToken(token);
      fetchUser();
    } else {
      setLoading(false);
    }

    // Listen for logout events
    const handleLogout = () => {
      sessionStorage.removeItem('auth_token');
      setAuthToken(null);
      setUser(null);
    };
    window.addEventListener('auth:logout', handleLogout);
    return () => window.removeEventListener('auth:logout', handleLogout);
  }, []);

  const fetchUser = async () => {
    try {
      const res = await authAPI.getMe();
      setUser(res.data);
    } catch {
      sessionStorage.removeItem('auth_token');
      setAuthToken(null);
    }
    setLoading(false);
  };

  const login = (token) => {
    sessionStorage.setItem('auth_token', token);
    setAuthToken(token);
    fetchUser();
  };

  const logout = () => {
    sessionStorage.removeItem('auth_token');
    setAuthToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);