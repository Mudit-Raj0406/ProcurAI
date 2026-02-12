"use client";

import React, { createContext, useState, useEffect, useContext } from 'react';
import { useRouter } from 'next/navigation';
import api from '../lib/api';

interface User {
    email: string;
    role: string;
}

interface AuthContextType {
    user: User | null;
    login: (token: string, role: string, email: string) => void;
    logout: () => void;
    loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        const token = localStorage.getItem('token');
        const role = localStorage.getItem('role');
        const email = localStorage.getItem('email');

        if (token && role && email) {
            setUser({ email, role });
            // Configure axios for future requests
            api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        }
        setLoading(false);
    }, []);

    const login = (token: string, role: string, email: string) => {
        localStorage.setItem('token', token);
        localStorage.setItem('role', role);
        localStorage.setItem('email', email);
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        setUser({ email, role });
        router.push('/');
    };

    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('role');
        localStorage.removeItem('email');
        delete api.defaults.headers.common['Authorization'];
        setUser(null);
        // Force a page refresh to clear all states and redirect
        window.location.href = '/login';
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
