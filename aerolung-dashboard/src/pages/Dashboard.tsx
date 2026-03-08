import React, { useState, useEffect, useCallback } from 'react';
import { AreaChart, Area, Line, XAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import {
    predictRisk, fetchDashboardStats, fetchHealthTrends, fetchPollutants, fetchCitiesAQI,
    type RiskPredictionRequest, type RiskPredictionResponse,
    type DashboardStats, type HealthTrend, type Pollutant, type CityAQI
} from '../services/api';

export default function Dashboard() {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [healthTrends, setHealthTrends] = useState<HealthTrend[]>([]);
    const [pollutants, setPollutants] = useState<Pollutant[]>([]);
    const [cityAqis, setCityAqis] = useState<CityAQI[]>([]);
    const [dataError, setDataError] = useState<string | null>(null);

    // FIX: Wrapped in useCallback so the interval always calls a stable reference
    const loadDashboardData = useCallback(async () => {
        try {
            setDataError(null);
            const [statsData, trendsData, pollutantsData, citiesAqiData] = await Promise.all([
                fetchDashboardStats(),
                fetchHealthTrends(),
                fetchPollutants(),
                fetchCitiesAQI()
            ]);
            setStats(statsData);
            setHealthTrends(trendsData);
            setPollutants(pollutantsData);
            setCityAqis(citiesAqiData);
        } catch (err) {
            console.error("Failed to load dashboard data", err);
            setDataError("Failed to load dashboard data. Retrying...");
        }
    }, []);

    useEffect(() => {
        loadDashboardData();
        const interval = setInterval(loadDashboardData, 30000);
        return () => clearInterval(interval);
    }, [loadDashboardData]);

    const [riskForm, setRiskForm] = useState<RiskPredictionRequest>({
        aqi: 150,
        spo2: 98,
        age: 45,
        smoker: false,
        asthma: false,
        heart_rate: 75
    });
    const [prediction, setPrediction] = useState<RiskPredictionResponse | null>(null);
    const [isPredicting, setIsPredicting] = useState(false);
    // FIX: User-facing error state for prediction failures
    const [predictionError, setPredictionError] = useState<string | null>(null);
    // FIX: Controlled state for city select so it resets after selection
    const [selectedCity, setSelectedCity] = useState('');

    const handlePredict = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsPredicting(true);
        setPredictionError(null);
        try {
            const result = await predictRisk(riskForm);
            setPrediction(result);
        } catch (error) {
            console.error("Failed prediction", error);
            // FIX: Show error to user instead of silently logging
            setPredictionError("Prediction failed. Please check your inputs and try again.");
        } finally {
            setIsPredicting(false);
        }
    };

    const handleCitySelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const city = e.target.value;
        setSelectedCity(city);
        const selectedAqi = cityAqis.find(c => c.city === city)?.aqi;
        if (selectedAqi !== undefined) {
            setRiskForm(prev => ({ ...prev, aqi: selectedAqi }));
        }
        // FIX: Reset select back to placeholder after applying the AQI value
        setTimeout(() => setSelectedCity(''), 300);
    };

    const getRiskColor = (level: string | undefined) => {
        switch (level) {
            case 'LOW':      return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
            case 'MODERATE': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
            case 'HIGH':     return 'text-orange-500 bg-orange-500/10 border-orange-500/20';
            case 'CRITICAL': return 'text-red-500 bg-red-500/10 border-red-500/20';
            default:         return 'text-slate-500 bg-slate-500/10 border-slate-500/20';
        }
    };

    return (
        <div className="flex-1 overflow-y-auto p-8 space-y-8">
            {/* Data load error banner */}
            {dataError && (
                <div className="flex items-center gap-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-medium">
                    <span className="material-symbols-outlined text-sm">warning</span>
                    {dataError}
                    <button onClick={() => setDataError(null)} className="ml-auto">
                        <span className="material-symbols-outlined text-sm">close</span>
                    </button>
                </div>
            )}

            {/* Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="glass p-6 rounded-2xl border border-white/10">
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-2 bg-blue-500/10 text-blue-500 rounded-lg">
                            <span className="material-symbols-outlined">person</span>
                        </div>
                        <span className="text-[10px] font-bold text-emerald-500 px-2 py-1 bg-emerald-500/10 rounded-full">
                            {stats?.users_trend ?? "..."}
                        </span>
                    </div>
                    <h3 className="text-slate-500 dark:text-slate-400 text-xs font-medium uppercase tracking-wider">Total Active Users</h3>
                    <p className="text-2xl font-bold mt-1">
                        {stats ? stats.total_users.toLocaleString() : "..."}
                    </p>
                </div>

                <div className="glass p-6 rounded-2xl border border-white/10">
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-2 bg-emerald-500/10 text-emerald-500 rounded-lg">
                            <span className="material-symbols-outlined">air</span>
                        </div>
                        <div className="flex gap-1 items-center">
                            <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                            {/* FIX: ?? instead of || so "0" doesn't show "..." */}
                            <span className="text-[10px] font-bold text-emerald-500">{stats?.aqi_status ?? "..."}</span>
                        </div>
                    </div>
                    <h3 className="text-slate-500 dark:text-slate-400 text-xs font-medium uppercase tracking-wider">Average City AQI</h3>
                    {/* FIX: ?? instead of || */}
                    <p className="text-2xl font-bold mt-1">{stats?.avg_aqi ?? "..."} <span className="text-sm font-normal text-slate-400">AQI</span></p>
                </div>

                <div className="glass p-6 rounded-2xl border border-white/10">
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-2 bg-amber-500/10 text-amber-500 rounded-lg">
                            <span className="material-symbols-outlined">warning</span>
                        </div>
                    </div>
                    <h3 className="text-slate-500 dark:text-slate-400 text-xs font-medium uppercase tracking-wider">High Risk Alerts</h3>
                    {/* FIX: ?? instead of || */}
                    <p className="text-2xl font-bold mt-1">{stats?.active_alerts ?? "..."} <span className="text-sm font-normal text-amber-500/80">Active</span></p>
                </div>

                <div className="glass p-6 rounded-2xl border border-white/10">
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-2 bg-primary/10 text-primary rounded-lg">
                            <span className="material-symbols-outlined">local_hospital</span>
                        </div>
                        {/* admissions_trend is a valid material icon name ("trending_down") from the API */}
                        <span className="text-primary material-symbols-outlined text-sm">
                            {stats?.admissions_trend ?? "trending_up"}
                        </span>
                    </div>
                    <h3 className="text-slate-500 dark:text-slate-400 text-xs font-medium uppercase tracking-wider">Hospital Admissions</h3>
                    {/* FIX: ?? instead of || */}
                    <p className="text-2xl font-bold mt-1">{stats?.hospital_admissions ?? "..."} <span className="text-sm font-normal text-slate-400">Total</span></p>
                </div>
            </div>

            {/* Center Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Map Section */}
                <div className="lg:col-span-2 glass rounded-2xl overflow-hidden relative min-h-[400px] border border-white/10">
                    <div className="absolute inset-0 map-gradient opacity-60 z-0 dark:text-white"></div>
                    <img
                        alt="Metropolitan Map"
                        className="absolute inset-0 w-full h-full object-cover mix-blend-overlay opacity-30 grayscale"
                        src="https://lh3.googleusercontent.com/aida-public/AB6AXuDC7K8YPXCpkecYz099fnEI0GeG39INIQIBpo4OsepKSOYUkdiIR39LtapQ58KzN9qnXwNNl__Zz3ClbyMFjfkbaIraOdp9ORxQ9AHoMifcEzGseBITKuDW7UiYQl_u9dEI0KODJA666AI_gLr42p0gJweUavp62Q5UHM216JZbf7fWEx6fZQ5xJPsbGo5j2QVEEtErXnKKiex47dHy918cmJofYDV3i06sMzQjn4jsiPzl_L6SL2PE0BxlKCoWfGrqEIL87L62BGM"
                    />
                    <div className="relative z-10 p-6 flex flex-col h-full">
                        <div className="flex justify-between items-center mb-6">
                            <div>
                                <h3 className="text-lg font-bold">Real-time Air Quality Map</h3>
                                <p className="text-sm text-slate-400">Live monitoring of Chicago Metropolitan Area</p>
                            </div>
                            <div className="flex gap-2">
                                <button className="px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-xs font-medium border border-white/10 transition-colors">PM 2.5</button>
                                <button className="px-3 py-1.5 bg-primary text-white rounded-lg text-xs font-medium transition-colors">Heat Zones</button>
                            </div>
                        </div>
                        <div className="flex-1 relative">
                            <div className="absolute top-1/4 left-1/3 p-2 glass rounded-lg flex items-center gap-2 border-emerald-500/50">
                                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                                <span className="text-xs font-bold">North Side: 24 AQI</span>
                            </div>
                            <div className="absolute bottom-1/3 right-1/4 p-2 glass rounded-lg flex items-center gap-2 border-red-500/50">
                                <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
                                <span className="text-xs font-bold">Industrial Hub: 156 AQI</span>
                            </div>
                            <div className="absolute top-2/3 left-1/2 p-2 glass rounded-lg flex items-center gap-2 border-purple-500/50">
                                <div className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></div>
                                <span className="text-xs font-bold">Downtown: 88 AQI</span>
                            </div>
                        </div>
                        <div className="mt-auto flex justify-between items-end">
                            <div className="glass p-3 rounded-xl flex gap-4 border border-white/10">
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded bg-emerald-500"></div>
                                    <span className="text-[10px] text-slate-300 uppercase font-bold">Clean</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded bg-amber-500"></div>
                                    <span className="text-[10px] text-slate-300 uppercase font-bold">Moderate</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded bg-red-500"></div>
                                    <span className="text-[10px] text-slate-300 uppercase font-bold">High Risk</span>
                                </div>
                            </div>
                            <div className="flex flex-col gap-1">
                                <button className="w-10 h-10 glass border border-white/10 rounded-lg flex items-center justify-center hover:bg-white/10 transition-colors">
                                    <span className="material-symbols-outlined">add</span>
                                </button>
                                <button className="w-10 h-10 glass border border-white/10 rounded-lg flex items-center justify-center hover:bg-white/10 transition-colors">
                                    <span className="material-symbols-outlined">remove</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Health Trends Section */}
                <div className="glass border border-white/10 rounded-2xl p-6 flex flex-col">
                    <h3 className="text-lg font-bold mb-1">Population Health Trends</h3>
                    <p className="text-sm text-slate-400 mb-6">Respiratory Health Score vs 30 Days</p>
                    <div className="flex-1 flex flex-col justify-end">
                        <div className="h-48 w-full relative -ml-4">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={healthTrends} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="colorHealth" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#3c83f6" stopOpacity={0.4} />
                                            <stop offset="95%" stopColor="#3c83f6" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b', fontWeight: 'bold' }} axisLine={false} tickLine={false} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'rgba(30, 41, 59, 0.8)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                                        itemStyle={{ color: '#fff' }}
                                    />
                                    <Area type="monotone" dataKey="health" stroke="#3c83f6" strokeWidth={3} fillOpacity={1} fill="url(#colorHealth)" />
                                    <Line type="monotone" dataKey="pollution" stroke="#ef4444" strokeWidth={2} strokeDasharray="4 4" dot={false} />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="mt-8 space-y-4">
                            <div className="flex justify-between items-center text-sm">
                                <span className="text-slate-400">Avg. Health Score</span>
                                <span className="font-bold">
                                    {healthTrends.length > 0 ? healthTrends[healthTrends.length - 1].health : "..."} / 100
                                </span>
                            </div>
                            <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-primary rounded-full transition-all duration-1000"
                                    style={{ width: `${healthTrends.length > 0 ? healthTrends[healthTrends.length - 1].health : 0}%` }}
                                ></div>
                            </div>
                            <div className="flex justify-between items-center text-xs">
                                <div className="flex items-center gap-1.5 text-emerald-500">
                                    <span className="material-symbols-outlined text-sm">trending_up</span>
                                    <span>+5% improvement</span>
                                </div>
                                <span className="text-slate-500">Last updated: 2h ago</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Bottom Row */}
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 pb-8">
                {/* High Risk Zones Table */}
                <div className="glass flex flex-col border border-white/10 rounded-2xl p-6 xl:col-span-1">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="font-bold">High Risk Zones</h3>
                        <button className="text-xs text-primary font-bold hover:underline">View All</button>
                    </div>
                    <div className="space-y-4 flex-1">
                        <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded bg-red-500/20 text-red-500 flex items-center justify-center">
                                    <span className="material-symbols-outlined text-lg">location_on</span>
                                </div>
                                <div>
                                    <p className="text-xs font-bold">South East Sector</p>
                                    <p className="text-[10px] text-slate-500">Industrial Area</p>
                                </div>
                            </div>
                            <div className="text-right">
                                <p className="text-xs font-bold text-red-500">182 AQI</p>
                                <p className="text-[10px] text-slate-500">Pop: 12.4k</p>
                            </div>
                        </div>

                        <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded bg-amber-500/20 text-amber-500 flex items-center justify-center">
                                    <span className="material-symbols-outlined text-lg">location_on</span>
                                </div>
                                <div>
                                    <p className="text-xs font-bold">Central Station</p>
                                    <p className="text-[10px] text-slate-500">Transit Hub</p>
                                </div>
                            </div>
                            <div className="text-right">
                                <p className="text-xs font-bold text-amber-500">114 AQI</p>
                                <p className="text-[10px] text-slate-500">Pop: 45.1k</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Pollutant Distribution Donut */}
                <div className="glass border border-white/10 rounded-2xl p-6">
                    <h3 className="font-bold mb-6">Pollutant Distribution</h3>
                    <div className="flex h-40 items-center justify-center gap-6">
                        <div className="relative h-40 w-40 flex items-center justify-center">
                            <ResponsiveContainer width={160} height={160}>
                                <PieChart>
                                    <Pie
                                        data={pollutants}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={55}
                                        outerRadius={70}
                                        paddingAngle={5}
                                        dataKey="value"
                                        stroke="none"
                                    >
                                        {pollutants.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.fill} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'rgba(30, 41, 59, 0.8)', border: 'none', borderRadius: '8px' }}
                                        itemStyle={{ color: '#fff' }}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                                <p className="text-2xl font-bold">Total</p>
                                <p className="text-[10px] text-slate-400 font-bold uppercase">Particles</p>
                            </div>
                        </div>

                        <div className="flex flex-col justify-center gap-4">
                            {pollutants.map((data) => (
                                <div key={data.name} className="flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: data.fill }}></div>
                                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wide">
                                        {data.name} ({data.value}%)
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* ML Risk Assessment Form */}
                <div className="glass flex flex-col border border-white/10 rounded-2xl p-6">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="font-bold">AI Risk Assessment</h3>
                        <div className="flex items-center gap-3">
                            {/* FIX: Controlled select with selectedCity state — resets after applying AQI */}
                            <select
                                value={selectedCity}
                                className="bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-lg px-2 py-1 text-xs text-slate-900 dark:text-slate-300 outline-none focus:ring-1 focus:ring-primary"
                                onChange={handleCitySelect}
                            >
                                <option value="">Select City AQI...</option>
                                {cityAqis.map(c => (
                                    <option key={c.city} value={c.city}>{c.city} ({c.aqi})</option>
                                ))}
                            </select>
                            <div className="p-1.5 bg-primary/10 rounded-lg">
                                <span className="material-symbols-outlined text-primary text-base">psychiatry</span>
                            </div>
                        </div>
                    </div>

                    <form onSubmit={handlePredict} className="space-y-4 flex-1 flex flex-col">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="text-xs text-slate-500 dark:text-slate-400 font-bold uppercase block mb-1">Local AQI</label>
                                <input
                                    type="number"
                                    className="w-full bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-white"
                                    value={riskForm.aqi}
                                    onChange={e => setRiskForm({ ...riskForm, aqi: parseInt(e.target.value) || 0 })}
                                />
                            </div>
                            <div>
                                <label className="text-xs text-slate-500 dark:text-slate-400 font-bold uppercase block mb-1">SpO2 (%)</label>
                                {/* FIX: parseFloat + step="0.1" — preserves decimal values like 98.5 */}
                                <input
                                    type="number"
                                    step="0.1"
                                    min="0"
                                    max="100"
                                    className="w-full bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-white"
                                    value={riskForm.spo2}
                                    onChange={e => setRiskForm({ ...riskForm, spo2: parseFloat(e.target.value) || 0 })}
                                />
                            </div>
                            <div>
                                <label className="text-xs text-slate-500 dark:text-slate-400 font-bold uppercase block mb-1">Age</label>
                                <input
                                    type="number"
                                    className="w-full bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-white"
                                    value={riskForm.age}
                                    onChange={e => setRiskForm({ ...riskForm, age: parseInt(e.target.value) || 0 })}
                                />
                            </div>
                            <div>
                                <label className="text-xs text-slate-500 dark:text-slate-400 font-bold uppercase block mb-1">Heart Rate</label>
                                <input
                                    type="number"
                                    className="w-full bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-white"
                                    value={riskForm.heart_rate}
                                    onChange={e => setRiskForm({ ...riskForm, heart_rate: parseInt(e.target.value) || 0 })}
                                />
                            </div>
                        </div>

                        <div className="flex justify-between mt-2 pt-2 border-t border-slate-200 dark:border-white/10">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    className="accent-primary"
                                    checked={riskForm.smoker}
                                    onChange={e => setRiskForm({ ...riskForm, smoker: e.target.checked })}
                                />
                                <span className="text-sm">Smoker</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    className="accent-primary"
                                    checked={riskForm.asthma}
                                    onChange={e => setRiskForm({ ...riskForm, asthma: e.target.checked })}
                                />
                                <span className="text-sm">Asthma</span>
                            </label>
                        </div>

                        {/* FIX: Show prediction error to user */}
                        {predictionError && (
                            <div className="flex items-center gap-2 p-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                                <span className="material-symbols-outlined text-sm">error</span>
                                <span className="flex-1">{predictionError}</span>
                                <button type="button" onClick={() => setPredictionError(null)}>
                                    <span className="material-symbols-outlined text-sm">close</span>
                                </button>
                            </div>
                        )}

                        <div className="mt-auto pt-4">
                            <button
                                type="submit"
                                disabled={isPredicting}
                                className="w-full bg-primary hover:bg-primary/90 disabled:opacity-60 text-white font-bold py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
                            >
                                {isPredicting ? (
                                    <span className="material-symbols-outlined animate-spin">refresh</span>
                                ) : (
                                    <>
                                        Evaluate Patient
                                        <span className="material-symbols-outlined text-sm">arrow_forward</span>
                                    </>
                                )}
                            </button>
                        </div>
                    </form>

                    {/* Result Overlay */}
                    {prediction && (
                        <div className="mt-4 p-4 rounded-xl border border-slate-200 dark:border-white/10 bg-slate-50 dark:bg-[#0b0f1a] relative overflow-hidden">
                            <button
                                onClick={() => setPrediction(null)}
                                className="absolute top-2 right-2 text-slate-400 hover:text-slate-600 dark:hover:text-white"
                            >
                                <span className="material-symbols-outlined text-sm">close</span>
                            </button>
                            <p className="text-xs text-slate-500 dark:text-slate-400 uppercase font-bold mb-1">Predicted Risk Level</p>
                            <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-lg border ${getRiskColor(prediction.risk_level)}`}>
                                <span className="material-symbols-outlined text-sm">
                                    {prediction.risk_level === 'CRITICAL' ? 'warning' : 'health_and_safety'}
                                </span>
                                <span className="font-black tracking-wide">{prediction.risk_level}</span>
                            </div>
                            {prediction.detailed_analysis?.plsi_score !== undefined && (
                                <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                                    PLSI Score:{' '}
                                    <span className="font-bold text-slate-700 dark:text-slate-200">
                                        {String(prediction.detailed_analysis.plsi_score)}
                                    </span>
                                </p>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
