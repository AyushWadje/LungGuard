import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { login as apiLogin, logout as apiLogout } from '../services/api';

const TOKEN_KEY = 'aerolung_token';
const TOKEN_EXPIRY_KEY = 'aerolung_token_expiry';
const TOKEN_LIFETIME_MS = 24 * 60 * 60 * 1000; // 24 hours

interface AuthContextType {
    isAuthenticated: boolean;
    token: string | null;
    login: (email: string, pass: string) => Promise<void>;
    // FIX: was typed as () => void but implementation is async — corrected to Promise<void>
    logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

function isTokenValid(): boolean {
    const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
    if (!expiry) return false;
    return Date.now() < parseInt(expiry, 10);
}

function getStoredToken(): string | null {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token && isTokenValid()) {
        return token;
    }
    // Token expired or missing — clean up
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
    return null;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [token, setToken] = useState<string | null>(() => getStoredToken());

    const isAuthenticated = !!token;

    useEffect(() => {
        if (token) {
            localStorage.setItem(TOKEN_KEY, token);
            if (!localStorage.getItem(TOKEN_EXPIRY_KEY)) {
                localStorage.setItem(TOKEN_EXPIRY_KEY, String(Date.now() + TOKEN_LIFETIME_MS));
            }
        } else {
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(TOKEN_EXPIRY_KEY);
        }
    }, [token]);

    // Periodically check token expiry
    useEffect(() => {
        const interval = setInterval(() => {
            if (token && !isTokenValid()) {
                console.warn('Token expired. Logging out.');
                setToken(null);
            }
        }, 60000);
        return () => clearInterval(interval);
    }, [token]);

    const login = useCallback(async (email: string, pass: string) => {
        const data = await apiLogin(email, pass);
        localStorage.setItem(TOKEN_EXPIRY_KEY, String(Date.now() + TOKEN_LIFETIME_MS));
        setToken(data.access_token);
    }, []);

    // FIX: Return type is now Promise<void> matching the interface
    const logout = useCallback(async (): Promise<void> => {
        try {
            await apiLogout();
        } catch (e) {
            console.error('Logout API failed', e);
        } finally {
            setToken(null);
        }
    }, []);

    return (
        <AuthContext.Provider value={{ isAuthenticated, token, login, logout }}>
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
