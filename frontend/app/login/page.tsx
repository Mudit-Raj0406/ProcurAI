"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';
import GlassCard from '../../components/GlassCard';
import api from '../../lib/api';
import { KeyRound, Mail, Loader2, ArrowRight, User } from 'lucide-react';

export default function LoginPage() {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [role, setRole] = useState('sourcing_buyer'); // Default role for signup
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const { login, user, logout } = useAuth();
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            if (isLogin) {
                // LOGIN LOGIC
                const formData = new FormData();
                formData.append('username', email);
                formData.append('password', password);

                const response = await api.post('/auth/token', formData, {
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
                });

                const { access_token, role } = response.data;
                login(access_token, role, email);
            } else {
                // SIGNUP LOGIC
                await api.post('/auth/signup', {
                    email,
                    password,
                    full_name: fullName,
                    role: role
                });

                // Auto-switch to login after successful signup
                setIsLogin(true);
                setError("Account created! Please sign in.");
                // Optional: Auto-login could be implemented, but strict flow is safer
            }
        } catch (err: any) {
            console.error(err);
            let errorMessage = "An unexpected error occurred";
            if (err.response) {
                // Server responded with a status code
                if (err.response.data?.detail) {
                    errorMessage = typeof err.response.data.detail === 'string'
                        ? err.response.data.detail
                        : JSON.stringify(err.response.data.detail);
                } else {
                    errorMessage = `Server Error: ${err.response.status}`;
                }
            } else if (err.request) {
                // Request made but no response (Network Error)
                errorMessage = "Network Error: Cannot reach server";
            } else {
                errorMessage = err.message;
            }
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen flex items-center justify-center p-8">
            <div className="w-full max-w-md">
                <header className="mb-8 text-center">
                    <h1 className="text-5xl font-black text-white drop-shadow-lg mb-2 tracking-tight">
                        ProcurAI
                    </h1>
                    <p className="text-lg text-white/80 font-light tracking-wide uppercase">
                        {isLogin ? "Secure Access" : "Join the Platform"}
                    </p>
                </header>

                {user ? (
                    <GlassCard className="text-center py-10">
                        <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-6 border border-blue-500/30">
                            <User className="w-8 h-8 text-blue-400" />
                        </div>
                        <h2 className="text-2xl font-bold text-white mb-2">Already Authenticated</h2>
                        <p className="text-white/60 mb-8">
                            You are currently signed in as <span className="text-blue-300 font-bold">{user.email}</span>
                        </p>
                        <div className="flex flex-col gap-3">
                            <button
                                onClick={() => router.push('/')}
                                className="w-full py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold transition-all shadow-lg hover:shadow-blue-500/30"
                            >
                                Go to Dashboard
                            </button>
                            <button
                                onClick={logout}
                                className="w-full py-4 bg-white/5 hover:bg-white/10 text-white rounded-xl font-bold transition-all border border-white/10"
                            >
                                Sign Out & Switch Account
                            </button>
                        </div>
                    </GlassCard>
                ) : (
                    <GlassCard className="transform transition-all duration-500 hover:scale-[1.01] border-white/10 shadow-2xl">
                        <div className="flex mb-8 bg-white/5 p-1 rounded-xl border border-white/5">
                            <button
                                onClick={() => { setIsLogin(true); setError(null); }}
                                className={`flex-1 py-2.5 rounded-lg text-sm font-bold transition-all ${isLogin ? 'bg-white/15 text-white shadow-lg' : 'text-white/40 hover:text-white/60 hover:bg-white/5'}`}
                            >
                                Log In
                            </button>
                            <button
                                onClick={() => { setIsLogin(false); setError(null); }}
                                className={`flex-1 py-2.5 rounded-lg text-sm font-bold transition-all ${!isLogin ? 'bg-white/15 text-white shadow-lg' : 'text-white/40 hover:text-white/60 hover:bg-white/5'}`}
                            >
                                Sign Up
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-6">
                            {!isLogin && (
                                <>
                                    <div>
                                        <label className="block text-sm font-semibold text-white/80 mb-2 uppercase tracking-wider">
                                            Full Name
                                        </label>
                                        <input
                                            type="text"
                                            required
                                            value={fullName}
                                            onChange={(e) => setFullName(e.target.value)}
                                            className="w-full px-5 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-white/50 transition-all backdrop-blur-sm"
                                            placeholder="John Doe"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-semibold text-white/80 mb-2 uppercase tracking-wider">
                                            Role
                                        </label>
                                        <select
                                            value={role}
                                            onChange={(e) => setRole(e.target.value)}
                                            className="w-full px-5 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-white/50 transition-all backdrop-blur-sm"
                                        >
                                            <option value="sourcing_buyer" className="text-gray-900">Sourcing Buyer</option>
                                            <option value="qa_manager" className="text-gray-900">QA Manager</option>
                                            <option value="procurement_manager" className="text-gray-900">Procurement Manager</option>
                                        </select>
                                    </div>
                                </>
                            )}

                            <div>
                                <label className="block text-sm font-semibold text-white/80 mb-2 uppercase tracking-wider">
                                    Email Address
                                </label>
                                <div className="relative">
                                    <Mail className="absolute left-4 top-3.5 w-5 h-5 text-white/50" />
                                    <input
                                        type="email"
                                        required
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="w-full pl-12 pr-5 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-white/50 transition-all backdrop-blur-sm"
                                        placeholder="user@example.com"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-white/80 mb-2 uppercase tracking-wider">
                                    Password
                                </label>
                                <div className="relative">
                                    <KeyRound className="absolute left-4 top-3.5 w-5 h-5 text-white/50" />
                                    <input
                                        type="password"
                                        required
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="w-full pl-12 pr-5 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-white/50 transition-all backdrop-blur-sm"
                                        placeholder="••••••••"
                                    />
                                </div>
                            </div>

                            {error && (
                                <div className={`p-3 rounded-lg text-center text-sm backdrop-blur-md border ${error.includes("created") ? "bg-green-500/20 border-green-500/30 text-green-200" : "bg-red-500/20 border-red-500/30 text-red-200"}`}>
                                    {error}
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={loading}
                                className={`w-full py-4 rounded-lg font-bold text-white shadow-lg transition-all duration-300 flex items-center justify-center gap-2
                                    ${loading
                                        ? 'bg-blue-600/50 cursor-not-allowed'
                                        : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-400 hover:to-purple-500 hover:shadow-blue-500/30'}
                                `}
                            >
                                {loading ? (
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                ) : (
                                    <>
                                        {isLogin ? "Sign In" : "Create Account"} <ArrowRight className="w-5 h-5" />
                                    </>
                                )}
                            </button>
                        </form>

                        <div className="mt-8 text-center">
                            <button
                                onClick={() => { setIsLogin(!isLogin); setError(null); }}
                                className="text-sm font-medium text-white/60 hover:text-white transition-colors flex items-center justify-center gap-2 mx-auto px-4 py-2 rounded-lg hover:bg-white/5"
                            >
                                {isLogin ? (
                                    <>Need an account? <span className="text-blue-400 border-b border-blue-400/30 font-bold">Sign Up</span></>
                                ) : (
                                    <>Already part of the team? <span className="text-blue-400 border-b border-blue-400/30 font-bold">Log In</span></>
                                )}
                            </button>
                        </div>
                    </GlassCard>
                )}
            </div>
        </main>
    );
}
