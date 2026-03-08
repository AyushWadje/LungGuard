import { Outlet, Link, useLocation, useNavigate } from "react-router-dom";
import { useState, useEffect, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import { fetchProfile, type UserProfile } from "../services/api";
import { cn } from "../lib/utils";

export default function Layout() {
    const location = useLocation();
    const navigate = useNavigate();
    const { logout } = useAuth();
    const [profile, setProfile] = useState<UserProfile | null>(null);
    // FIX: Controlled search state
    const [searchQuery, setSearchQuery] = useState('');
    // FIX: Notifications panel state
    const [showNotifications, setShowNotifications] = useState(false);
    const notifRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        fetchProfile().then(setProfile).catch(console.error);
    }, []);

    // FIX: Close notifications panel when clicking outside
    useEffect(() => {
        function handleClickOutside(e: MouseEvent) {
            if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
                setShowNotifications(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Theme state
    const [isDarkMode, setIsDarkMode] = useState(() => {
        const stored = localStorage.getItem("darkMode");
        return stored !== null ? JSON.parse(stored) : true;
    });

    useEffect(() => {
        if (isDarkMode) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
        localStorage.setItem("darkMode", JSON.stringify(isDarkMode));
    }, [isDarkMode]);

    const navItems = [
        { name: "Dashboard", path: "/", icon: "dashboard" },
        { name: "Population Health", path: "/population-health", icon: "groups" },
        { name: "Air Quality Map", path: "/air-quality-map", icon: "map" },
        { name: "Analytics", path: "/analytics", icon: "analytics" },
        { name: "Alerts", path: "/alerts", icon: "notifications" },
        { name: "Settings", path: "/settings", icon: "settings" },
    ];

    return (
        <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-[#1a1d29] font-display text-slate-900 dark:text-slate-100 antialiased transition-colors duration-300">
            {/* Sidebar */}
            <aside className="w-64 flex-shrink-0 border-r border-slate-200 dark:border-white/5 bg-white dark:bg-[#1a1d29] flex flex-col justify-between transition-colors duration-300">
                <div className="p-6">
                    <div className="flex flex-col mb-8">
                        <h1 className="text-primary text-xl font-bold tracking-tight">LungGuard AI</h1>
                        <p className="text-slate-500 dark:text-slate-400 text-xs font-medium uppercase tracking-wider">Med-Tech SaaS</p>
                    </div>
                    <nav className="space-y-1">
                        {navItems.map((item) => {
                            const isActive = location.pathname === item.path;
                            return (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    className={cn(
                                        "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                                        isActive
                                            ? "bg-primary/10 text-primary dark:bg-primary/20"
                                            : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-white/5 hover:text-slate-900 dark:hover:text-white"
                                    )}
                                >
                                    <span className={cn("material-symbols-outlined text-lg", isActive && "text-primary")}>
                                        {item.icon}
                                    </span>
                                    {item.name}
                                </Link>
                            );
                        })}
                    </nav>
                </div>

                {/* User Profile Section */}
                <div className="p-4 border-t border-slate-200 dark:border-white/5">
                    <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-white/5 cursor-pointer transition-colors">
                        <img
                            src={profile?.avatar_url || "https://i.pravatar.cc/150?img=5"}
                            alt="User avatar"
                            className="h-9 w-9 rounded-full object-cover border-2 border-primary/30"
                        />
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold truncate text-slate-900 dark:text-white">{profile?.name || "Loading..."}</p>
                            <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{profile?.role || "..."}</p>
                        </div>
                        <button
                            onClick={async () => {
                                // FIX: logout is async — await it before navigating
                                await logout();
                                navigate('/login');
                            }}
                            className="p-1 text-slate-400 hover:text-red-500 transition-colors"
                            title="Logout"
                        >
                            <span className="material-symbols-outlined text-lg">logout</span>
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col overflow-y-auto custom-scrollbar">
                {/* Top Bar */}
                <header className="flex items-center justify-between px-8 py-4 border-b border-slate-200 dark:border-white/5 bg-white/80 dark:bg-[#1a1d29]/80 backdrop-blur-md sticky top-0 z-30">
                    <div className="flex items-center gap-4 flex-1">
                        <div className="relative flex-1 max-w-md">
                            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-lg">search</span>
                            {/* FIX: Controlled search input */}
                            <input
                                className="w-full bg-slate-100 dark:bg-slate-800/50 border border-slate-200 dark:border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm focus:ring-2 focus:ring-primary/20 transition-all placeholder:text-slate-500 text-slate-800 dark:text-slate-100 outline-none shadow-sm dark:shadow-none"
                                placeholder="Search analytics, trends, or patient segments..."
                                type="text"
                                value={searchQuery}
                                onChange={e => setSearchQuery(e.target.value)}
                                onKeyDown={e => {
                                    if (e.key === 'Enter' && searchQuery.trim()) {
                                        navigate(`/analytics?q=${encodeURIComponent(searchQuery.trim())}`);
                                    }
                                }}
                            />
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setIsDarkMode(!isDarkMode)}
                            className="p-2 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-all focus:outline-none focus:ring-2 focus:ring-primary/50"
                            aria-label="Toggle Dark Mode"
                            title="Toggle Dark Mode"
                        >
                            <span className="material-symbols-outlined">
                                {isDarkMode ? 'light_mode' : 'dark_mode'}
                            </span>
                        </button>

                        <button className="p-2 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-all focus:outline-none focus:ring-2 focus:ring-primary/50 text-center">
                            <span className="material-symbols-outlined block">help</span>
                        </button>

                        <div className="h-6 w-px bg-slate-200 dark:bg-white/10 mx-1 border-r"></div>

                        {/* FIX: Notifications button now toggles a dropdown panel */}
                        <div className="relative" ref={notifRef}>
                            <button
                                onClick={() => setShowNotifications(v => !v)}
                                className="p-2 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-all relative focus:outline-none focus:ring-2 focus:ring-primary/50 text-center"
                                aria-label="Notifications"
                            >
                                <span className="material-symbols-outlined block">notifications</span>
                                <span className="absolute top-2.5 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white dark:border-[#1a1d29] shadow-sm"></span>
                            </button>

                            {showNotifications && (
                                <div className="absolute right-0 top-full mt-2 w-80 bg-white dark:bg-slate-900 border border-slate-200 dark:border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden">
                                    <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-white/10">
                                        <h4 className="text-sm font-bold text-slate-900 dark:text-white">Notifications</h4>
                                        <button
                                            onClick={() => setShowNotifications(false)}
                                            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                                        >
                                            <span className="material-symbols-outlined text-sm">close</span>
                                        </button>
                                    </div>
                                    <div className="divide-y divide-slate-100 dark:divide-white/5 max-h-72 overflow-y-auto">
                                        {[
                                            { icon: 'warning', color: 'text-red-500', bg: 'bg-red-500/10', title: 'Critical AQI Alert', desc: 'PM2.5 exceeded 200 µg/m³ in Industrial East', time: '2 min ago' },
                                            { icon: 'check_circle', color: 'text-emerald-500', bg: 'bg-emerald-500/10', title: 'Alert Resolved', desc: 'Harbor District PM10 levels normalized', time: '45 min ago' },
                                            { icon: 'analytics', color: 'text-primary', bg: 'bg-primary/10', title: 'Report Ready', desc: 'Monthly analytics report has been generated', time: '2 hrs ago' },
                                            { icon: 'person_add', color: 'text-purple-500', bg: 'bg-purple-500/10', title: 'New Team Member', desc: 'Dr. Patel joined your workspace', time: '1 day ago' },
                                        ].map((n, i) => (
                                            <div key={i} className="flex items-start gap-3 px-4 py-3 hover:bg-slate-50 dark:hover:bg-white/5 cursor-pointer transition-colors">
                                                <div className={`mt-0.5 h-8 w-8 rounded-full ${n.bg} flex items-center justify-center shrink-0`}>
                                                    <span className={`material-symbols-outlined text-sm ${n.color}`}>{n.icon}</span>
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-xs font-bold text-slate-900 dark:text-white">{n.title}</p>
                                                    <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 leading-tight">{n.desc}</p>
                                                    <p className="text-[10px] text-slate-400 mt-1">{n.time}</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                    <div className="px-4 py-2 border-t border-slate-200 dark:border-white/10">
                                        <Link
                                            to="/alerts"
                                            onClick={() => setShowNotifications(false)}
                                            className="block text-center text-xs font-bold text-primary hover:underline py-1"
                                        >
                                            View All Alerts →
                                        </Link>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </header>

                {/* Page Content */}
                <div className="mx-auto w-full transition-opacity duration-300">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
