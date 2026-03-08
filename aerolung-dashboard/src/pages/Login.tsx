import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await login(email, password);
            navigate('/');
        } catch (err: any) {
            setError(err.message || 'Login failed. Please check credentials.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-[#0b0f1a] flex items-center justify-center p-4 relative overflow-hidden">
            {/* Background Map Styling */}
            <div className="absolute inset-0 z-0">
                <img className="w-full h-full object-cover opacity-20 mix-blend-screen grayscale brightness-75 contrast-125" alt="Map background" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDSKpo0LjVwquEBWVs6LoeR-jM4UusHQjpSa5J0Sjb2QrUF6ygQGDlelrg571L53twWBA1YfiUi__wvGYcbCTn9orb40Na2guEPyCneIpwKQEYOjSmQHSYc7BLxQkfIiMXGEKCozVQeyI-6NgFnERbWo2hVNlka-2WJ3KQssBe_DLTTuKUghaQf2Sk_YP6L5ByFCKfGyG4QtxQrK55Cp3xiq2oNyWR-2AZfSxj-5XX8YZs0x_DF10sjoFXnJT-kFZd0O1lkD-hNoBg" />
                <div className="absolute top-1/4 left-1/3 size-64 bg-primary/20 rounded-full blur-3xl animate-pulse"></div>
            </div>

            <div className="relative z-10 w-full max-w-md glass-panel p-8 rounded-2xl shadow-2xl border border-white/20">
                <div className="flex items-center justify-center gap-3 mb-8">
                    <div className="h-10 w-10 bg-gradient-to-br from-primary to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-primary/30">
                        <span className="material-symbols-outlined text-white">air</span>
                    </div>
                    <div>
                        <h1 className="text-2xl font-black tracking-tight dark:text-white leading-none">AeroLung</h1>
                        <p className="text-[10px] uppercase tracking-widest text-primary font-bold">Health Intelligence</p>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                    {error && (
                        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm text-center">
                            {error}
                        </div>
                    )}

                    <div className="space-y-1">
                        <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Work Email</label>
                        <div className="relative">
                            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">mail</span>
                            <input
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full bg-slate-100 dark:bg-slate-900/50 border border-slate-300 dark:border-white/10 rounded-lg pl-10 pr-4 py-3 text-sm focus:ring-2 focus:ring-primary focus:border-transparent transition-all dark:text-white outline-none"
                                placeholder="dr.smith@hospital.org"
                            />
                        </div>
                    </div>

                    <div className="space-y-1">
                        <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Password</label>
                        <div className="relative">
                            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">lock</span>
                            <input
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-slate-100 dark:bg-slate-900/50 border border-slate-300 dark:border-white/10 rounded-lg pl-10 pr-4 py-3 text-sm focus:ring-2 focus:ring-primary focus:border-transparent transition-all dark:text-white outline-none"
                                placeholder="••••••••"
                            />
                        </div>
                    </div>

                    <div className="flex justify-end">
                        <a href="#" className="text-xs text-primary font-bold hover:underline">Forgot password?</a>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-3 rounded-lg bg-gradient-to-r from-primary to-blue-600 text-white font-bold text-sm shadow-lg shadow-primary/30 hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {loading ? 'Authenticating...' : 'Sign In Securely'}
                        {!loading && <span className="material-symbols-outlined text-sm">arrow_forward</span>}
                    </button>
                </form>

                <p className="mt-8 text-center text-xs text-slate-500 dark:text-slate-400">
                    Protected by AES-256 Encryption & Medical Grade Security.
                </p>
            </div>
        </div>
    );
}

