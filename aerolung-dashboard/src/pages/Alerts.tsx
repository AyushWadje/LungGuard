import { useState, useEffect, useMemo, useCallback } from 'react';
import { fetchActiveAlerts, acknowledgeAlert, issueAlertAdvisory, type ActiveAlert } from '../services/api';

export default function Alerts() {
    const [alerts, setAlerts] = useState<ActiveAlert[]>([]);
    const [severityFilter, setSeverityFilter] = useState('All');
    const [statusFilter, setStatusFilter] = useState('All');
    // FIX: Track which alert's details panel is expanded
    const [expandedAlertId, setExpandedAlertId] = useState<string | null>(null);
    // FIX: Track advisory success toast
    const [advisoryToast, setAdvisoryToast] = useState<string | null>(null);

    // FIX: Wrapped in useCallback so the setInterval always holds a stable reference
    const loadAlerts = useCallback(async () => {
        try {
            const data = await fetchActiveAlerts();
            setAlerts(data);
        } catch (err) {
            console.error("Failed to load alerts", err);
        }
    }, []);

    useEffect(() => {
        loadAlerts();
        const interval = setInterval(loadAlerts, 30000);
        return () => clearInterval(interval);
    }, [loadAlerts]);

    const handleAcknowledge = async (id: string) => {
        // FIX: Optimistically remove from UI immediately for instant feedback
        setAlerts(prev => prev.filter(a => a.id !== id));
        if (expandedAlertId === id) setExpandedAlertId(null);
        try {
            await acknowledgeAlert(id);
        } catch (e) {
            console.error(e);
            // Rollback on failure by reloading
            loadAlerts();
        }
    };

    const handleAdvisory = async (id: string) => {
        try {
            await issueAlertAdvisory(id);
            const alert = alerts.find(a => a.id === id);
            setAdvisoryToast(`Advisory issued for: ${alert?.title ?? id}`);
            setTimeout(() => setAdvisoryToast(null), 4000);
        } catch (e) {
            console.error(e);
        }
    };

    // FIX: Toggle details panel for "View Details" button
    const handleViewDetails = (id: string) => {
        setExpandedAlertId(prev => prev === id ? null : id);
    };

    const filteredAlerts = useMemo(() => {
        return alerts.filter(alert => {
            const matchesSeverity = severityFilter === 'All' || alert.severity.toLowerCase() === severityFilter.toLowerCase();
            const matchesStatus = statusFilter === 'All' || (alert as ActiveAlert & { status?: string }).status?.toLowerCase() === statusFilter.toLowerCase();
            return matchesSeverity && matchesStatus;
        });
    }, [alerts, severityFilter, statusFilter]);

    const totalAlerts = filteredAlerts.length;
    const totalPopulation = useMemo(() => filteredAlerts.reduce((acc, alert) => acc + alert.population, 0), [filteredAlerts]);

    return (
        <div className="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar">
            {/* Advisory Toast */}
            {advisoryToast && (
                <div className="fixed top-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm font-medium shadow-xl backdrop-blur-sm">
                    <span className="material-symbols-outlined text-sm">check_circle</span>
                    {advisoryToast}
                    <button onClick={() => setAdvisoryToast(null)} className="ml-2">
                        <span className="material-symbols-outlined text-sm">close</span>
                    </button>
                </div>
            )}

            {/* Header & Filters */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Alerts &amp; Response Management</h2>
                    <p className="text-slate-600 dark:text-slate-400 text-sm">Monitor and respond to real-time respiratory health threats.</p>
                </div>
                <div className="flex flex-wrap gap-2">
                    <div className="flex bg-slate-200 dark:bg-slate-800/50 p-1 rounded-lg border border-slate-300 dark:border-white/5">
                        <button onClick={() => setSeverityFilter('All')} className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${severityFilter === 'All' ? 'bg-primary shadow-sm text-white' : 'text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-300'}`}>All Severity</button>
                        <button onClick={() => setSeverityFilter('Critical')} className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${severityFilter === 'Critical' ? 'bg-primary shadow-sm text-white' : 'text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-300'}`}>Critical</button>
                        <button onClick={() => setSeverityFilter('High')} className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${severityFilter === 'High' ? 'bg-primary shadow-sm text-white' : 'text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-300'}`}>High</button>
                    </div>
                    <button
                        onClick={() => setStatusFilter(statusFilter === 'All' ? 'active' : 'All')}
                        className={`flex items-center gap-2 p-1.5 px-3 rounded-lg border text-sm transition-colors ${statusFilter !== 'All' ? 'bg-primary border-primary text-white' : 'bg-slate-200 dark:bg-slate-800/50 border-slate-300 dark:border-white/5 text-slate-700 dark:text-slate-300'}`}
                    >
                        <span className="material-symbols-outlined text-sm">filter_list</span>
                        <span className="text-sm">{statusFilter === 'All' ? 'Filter Status' : 'Active Only'}</span>
                    </button>
                </div>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="glass-card p-6 rounded-xl flex items-center justify-between">
                    <div>
                        <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Active Alerts</p>
                        <h3 className="text-3xl font-bold mt-1 text-slate-900 dark:text-white">{totalAlerts}</h3>
                        <p className="text-xs text-red-500 mt-2 flex items-center gap-1">
                            <span className="material-symbols-outlined text-[14px]">trending_up</span>
                            +20% from last hour
                        </p>
                    </div>
                    <div className="h-12 w-12 rounded-full bg-red-500/10 flex items-center justify-center text-red-500 pulse-red">
                        <span className="material-symbols-outlined">priority_high</span>
                    </div>
                </div>

                <div className="glass-card p-6 rounded-xl flex items-center justify-between">
                    <div>
                        <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Avg Response Time</p>
                        <h3 className="text-3xl font-bold mt-1 text-slate-900 dark:text-white">4.2 <span className="text-lg font-normal text-slate-500">mins</span></h3>
                        <p className="text-xs text-green-500 mt-2 flex items-center gap-1">
                            <span className="material-symbols-outlined text-[14px]">trending_down</span>
                            -12% improvement
                        </p>
                    </div>
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                        <span className="material-symbols-outlined">timer</span>
                    </div>
                </div>

                <div className="glass-card p-6 rounded-xl flex items-center justify-between">
                    <div>
                        <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Pop. at High Risk</p>
                        <h3 className="text-3xl font-bold mt-1 text-slate-900 dark:text-white">{(totalPopulation / 1000).toFixed(1)}k</h3>
                        <p className="text-xs text-slate-500 mt-2">Currently monitored regions</p>
                    </div>
                    <div className="flex bg-slate-200 dark:bg-slate-800/50 p-3 rounded-lg border border-slate-300 dark:border-white/5 text-primary">
                        <span className="material-symbols-outlined">groups</span>
                    </div>
                </div>
            </div>

            {/* Split Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left: Active Alerts List */}
                <div className="lg:col-span-2 space-y-4">
                    <div className="flex items-center justify-between mb-2">
                        <h4 className="font-bold text-lg text-slate-900 dark:text-white">Active Alerts</h4>
                        <span className="text-xs text-slate-500">Real-time stream</span>
                    </div>

                    {filteredAlerts.length === 0 && (
                        <div className="glass-card p-8 rounded-xl text-center text-slate-500">
                            <span className="material-symbols-outlined text-4xl mb-2 block text-emerald-500">check_circle</span>
                            No alerts match the current filters.
                        </div>
                    )}

                    {filteredAlerts.map((alert) => (
                        <div key={alert.id} className={`glass-card rounded-xl border-l-4 overflow-hidden ${alert.color === 'red' ? 'border-red-500 critical-glow' : 'border-orange-500'}`}>
                            <div className="p-5 relative">
                                {alert.color === 'red' && (
                                    <div className="absolute top-0 right-0 p-3 opacity-10 pointer-events-none">
                                        <span className="material-symbols-outlined text-6xl text-red-500">warning</span>
                                    </div>
                                )}
                                <div className="flex flex-col gap-4 relative z-10">
                                    <div className="flex items-start justify-between">
                                        <div className="space-y-1">
                                            <div className="flex items-center gap-2">
                                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider border ${alert.color === 'red' ? 'bg-red-500/20 text-red-500 border-red-500/30' : 'bg-orange-500/20 text-orange-500 border-orange-500/30'}`}>
                                                    {alert.severity}
                                                </span>
                                                <span className="text-xs text-slate-500">ID: {alert.id}</span>
                                            </div>
                                            <h5 className="text-lg font-bold text-slate-900 dark:text-white">{alert.title}</h5>
                                            <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                                                <span className="material-symbols-outlined text-sm">location_on</span>
                                                {alert.location}
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-sm font-semibold text-slate-900 dark:text-white">{alert.population.toLocaleString()}</p>
                                            <p className="text-[10px] text-slate-500 uppercase">Affected Population</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3 pt-2">
                                        {/* FIX: "View Details" now toggles an expanded details panel */}
                                        <button
                                            onClick={() => handleViewDetails(alert.id)}
                                            className="px-4 py-2 text-white text-xs font-bold rounded-lg transition-colors btn-gradient-primary flex items-center gap-1"
                                        >
                                            {expandedAlertId === alert.id ? 'Hide Details' : 'View Details'}
                                            <span className="material-symbols-outlined text-sm">
                                                {expandedAlertId === alert.id ? 'expand_less' : 'expand_more'}
                                            </span>
                                        </button>
                                        <button
                                            onClick={() => handleAdvisory(alert.id)}
                                            className="px-4 py-2 bg-slate-200 dark:bg-slate-800/80 text-slate-800 dark:text-white text-xs font-bold rounded-lg hover:bg-slate-300 dark:hover:bg-slate-700 transition-colors border border-slate-300 dark:border-white/5"
                                        >
                                            Issue Public Advisory
                                        </button>
                                        {/* FIX: Acknowledge now optimistically removes the alert from UI */}
                                        <button
                                            onClick={() => handleAcknowledge(alert.id)}
                                            className="ml-auto p-2 text-slate-500 dark:text-slate-400 hover:text-emerald-500 transition-colors"
                                            title="Acknowledge & dismiss alert"
                                        >
                                            <span className="material-symbols-outlined text-sm">check_circle</span>
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* FIX: Expanded details panel — shown when "View Details" is clicked */}
                            {expandedAlertId === alert.id && (
                                <div className="border-t border-slate-200 dark:border-white/10 bg-slate-50 dark:bg-slate-900/40 px-5 py-4 space-y-3">
                                    <h6 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Alert Intelligence</h6>
                                    <div className="grid grid-cols-2 gap-4 text-xs">
                                        <div>
                                            <p className="text-slate-500 dark:text-slate-400">Severity Level</p>
                                            <p className="font-bold text-slate-800 dark:text-white mt-0.5">{alert.severity}</p>
                                        </div>
                                        <div>
                                            <p className="text-slate-500 dark:text-slate-400">Alert ID</p>
                                            <p className="font-bold text-slate-800 dark:text-white mt-0.5">{alert.id}</p>
                                        </div>
                                        <div>
                                            <p className="text-slate-500 dark:text-slate-400">Location</p>
                                            <p className="font-bold text-slate-800 dark:text-white mt-0.5">{alert.location}</p>
                                        </div>
                                        <div>
                                            <p className="text-slate-500 dark:text-slate-400">Affected Population</p>
                                            <p className="font-bold text-slate-800 dark:text-white mt-0.5">{alert.population.toLocaleString()}</p>
                                        </div>
                                    </div>
                                    <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-600 dark:text-amber-400">
                                        <strong>Recommended Action:</strong>{' '}
                                        {alert.color === 'red'
                                            ? 'Immediate evacuation advisory and N95 mask distribution recommended for affected zones.'
                                            : 'Issue public health advisory and increase monitoring frequency in affected area.'}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                {/* Right: Alert Intelligence */}
                <div className="space-y-6">
                    {/* Mini Map */}
                    <div className="glass-card rounded-xl overflow-hidden">
                        <div className="p-4 border-b border-slate-200 dark:border-slate-700/50 flex justify-between items-center">
                            <h4 className="text-sm font-bold text-slate-900 dark:text-white">Regional Risk Heatmap</h4>
                            <span className="material-symbols-outlined text-slate-500 text-sm">open_in_full</span>
                        </div>
                        <div className="h-48 bg-slate-100 dark:bg-slate-900/50 relative overflow-hidden group">
                            <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-red-500/20"></div>
                            <div className="absolute top-1/4 left-1/3 h-12 w-12 bg-red-500/40 rounded-full blur-xl animate-pulse"></div>
                            <div className="absolute bottom-1/3 right-1/4 h-16 w-16 bg-orange-500/30 rounded-full blur-xl animate-pulse"></div>
                            <div className="absolute inset-0 flex items-center justify-center">
                                <p className="text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-widest font-bold">Live Data Feed</p>
                            </div>
                        </div>
                    </div>

                    {/* Predicted Escalation */}
                    <div className="glass-card p-4 rounded-xl">
                        <h4 className="text-sm font-bold text-slate-900 dark:text-white mb-4">Predicted Escalation</h4>
                        <div className="h-24 flex items-end gap-1 px-2">
                            <div className="flex-1 bg-primary/20 rounded-t h-[40%]"></div>
                            <div className="flex-1 bg-primary/20 rounded-t h-[35%]"></div>
                            <div className="flex-1 bg-primary/30 rounded-t h-[50%]"></div>
                            <div className="flex-1 bg-primary/40 rounded-t h-[65%]"></div>
                            <div className="flex-1 bg-gradient-to-t from-primary to-purple-500 opacity-70 rounded-t h-[85%]"></div>
                            <div className="flex-1 bg-gradient-to-t from-primary to-purple-500 rounded-t h-full"></div>
                            <div className="flex-1 bg-gradient-to-t from-primary to-purple-500 opacity-80 rounded-t h-[90%]"></div>
                        </div>
                        <div className="flex justify-between mt-2 text-[10px] text-slate-500 font-medium">
                            <span>Now</span>
                            <span>+2h</span>
                            <span>+4h</span>
                            <span>+6h</span>
                        </div>
                        <div className="mt-4 p-2 rounded-lg bg-red-500/10 border border-red-500/20">
                            <p className="text-[10px] text-red-400 leading-tight">
                                <strong>Trend Warning:</strong> Risk index in Industrial East expected to rise by 14% by midnight.
                            </p>
                        </div>
                    </div>

                    {/* Notification History */}
                    <div className="glass-card p-4 rounded-xl">
                        <h4 className="text-sm font-bold text-slate-900 dark:text-white mb-4">Notification History</h4>
                        <div className="space-y-4">
                            <div className="flex gap-3">
                                <div className="mt-1 h-2 w-2 rounded-full bg-slate-500 shrink-0"></div>
                                <div>
                                    <p className="text-xs text-slate-700 dark:text-slate-300">Advisory: School Zone Air Filter Alert issued</p>
                                    <p className="text-[10px] text-slate-500">12 mins ago</p>
                                </div>
                            </div>
                            <div className="flex gap-3">
                                <div className="mt-1 h-2 w-2 rounded-full bg-green-500 shrink-0"></div>
                                <div>
                                    <p className="text-xs text-slate-700 dark:text-slate-300">Alert Resolved: Harbor District PM10 levels back to normal</p>
                                    <p className="text-[10px] text-slate-500">45 mins ago</p>
                                </div>
                            </div>
                            <div className="flex gap-3">
                                <div className="mt-1 h-2 w-2 rounded-full bg-slate-500 shrink-0"></div>
                                <div>
                                    <p className="text-xs text-slate-700 dark:text-slate-300">System: Monthly risk aggregation report generated</p>
                                    <p className="text-[10px] text-slate-500">2 hours ago</p>
                                </div>
                            </div>
                        </div>
                        <button className="w-full mt-4 py-2 text-[10px] font-bold text-slate-500 hover:text-primary transition-colors uppercase tracking-widest">
                            View Full Audit Log
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
