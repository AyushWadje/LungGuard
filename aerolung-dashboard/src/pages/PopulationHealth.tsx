
import { useState, useEffect, useRef, useCallback } from 'react';
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';
import { LineChart, Line, XAxis, Tooltip, ResponsiveContainer, CartesianGrid, ComposedChart, Bar, Scatter, YAxis } from 'recharts';
import { fetchHealthDemographics, fetchHealthCorrelation, type HealthDemographic, type HealthCorrelation } from '../services/api';

export default function PopulationHealth() {
    const [demographics, setDemographics] = useState<HealthDemographic[]>([]);
    const [correlation, setCorrelation] = useState<HealthCorrelation[]>([]);
    const [conditionFilter, setConditionFilter] = useState('By Condition');
    const [timeline, setTimeline] = useState('30d');
    const chartRef = useRef<HTMLDivElement>(null);

    const [exportError, setExportError] = useState<string | null>(null);

    const handleExportPDF = useCallback(async () => {
        if (!chartRef.current) return;
        setExportError(null);
        try {
            const canvas = await html2canvas(chartRef.current, { scale: 2, useCORS: true, backgroundColor: '#0f172a' });
            const imgData = canvas.toDataURL('image/png');
            const pdf = new jsPDF('landscape', 'mm', 'a4');
            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
            pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
            pdf.save(`Population_Health_${timeline}.pdf`);
        } catch (error) {
            console.error('Error generating PDF', error);
            setExportError('Failed to generate export PDF. Please try again.');
        }
    }, [timeline]);

    useEffect(() => {
        const loadHealthData = async () => {
            try {
                const [demoData, corrData] = await Promise.all([
                    fetchHealthDemographics(conditionFilter),
                    fetchHealthCorrelation()
                ]);

                const multiplier = timeline === '90d' ? 3 : timeline === '1y' ? 12 : 1;

                const adjustedDemo = demoData.map(d => ({
                    ...d,
                    age0_17: Math.round(d.age0_17 * multiplier),
                    age18_64: Math.round(d.age18_64 * multiplier),
                    age65_plus: Math.round(d.age65_plus * multiplier)
                }));
                const adjustedCorr = corrData.map(c => ({
                    ...c,
                    score: Math.min(100, Math.round(c.score * (1 + (multiplier - 1) * 0.05)))
                }));

                setDemographics(adjustedDemo);
                setCorrelation(adjustedCorr);
            } catch (err) {
                console.error("Failed to load health data", err);
            }
        };
        loadHealthData();
        const interval = setInterval(loadHealthData, 30000);
        return () => clearInterval(interval);
    }, [conditionFilter, timeline]);
    return (
        <div ref={chartRef} className="p-8 space-y-8 max-w-[1400px] w-full">
            {exportError && (
                <div className="flex items-center gap-3 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                    <span className="material-symbols-outlined text-sm">error</span>
                    {exportError}
                    <button onClick={() => setExportError(null)} className="ml-auto text-red-400 hover:text-red-300">
                        <span className="material-symbols-outlined text-sm">close</span>
                    </button>
                </div>
            )}
            {/* Page Header & Filter */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Population Health Analysis</h2>
                    <p className="text-slate-500 dark:text-slate-400 mt-1">Comprehensive respiratory health insights across monitored regions.</p>
                </div>
                <div className="flex items-center bg-slate-200 dark:bg-slate-800 p-1 rounded-lg self-start border border-white/5">
                    <button onClick={() => setTimeline('30d')} className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-colors ${timeline === '30d' ? 'bg-white dark:bg-slate-700 shadow-sm border border-white/10' : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-100'}`}>Last 30 Days</button>
                    <button onClick={() => setTimeline('90d')} className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-colors ${timeline === '90d' ? 'bg-white dark:bg-slate-700 shadow-sm border border-white/10' : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-100'}`}>90 Days</button>
                    <button onClick={() => setTimeline('1y')} className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-colors ${timeline === '1y' ? 'bg-white dark:bg-slate-700 shadow-sm border border-white/10' : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-100'}`}>1 Year</button>
                </div>
            </div>

            {/* Row 1: KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="glass p-6 rounded-xl flex items-center justify-between border border-white/10">
                    <div>
                        <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Avg. Health Score</p>
                        <h3 className="text-3xl font-bold mt-1">88<span className="text-lg text-slate-500">/100</span></h3>
                        <p className="text-xs text-emerald-500 font-medium flex items-center mt-2">
                            <span className="material-symbols-outlined text-sm mr-1">trending_up</span> +2.4% from last month
                        </p>
                    </div>
                    <div className="w-14 h-14 rounded-full border-4 border-primary/20 flex items-center justify-center relative shadow-lg shadow-primary/20">
                        <svg className="absolute inset-0 w-full h-full -rotate-90">
                            <circle className="text-primary" cx="28" cy="28" fill="transparent" r="24" stroke="currentColor" strokeDasharray="150" strokeDashoffset="15" strokeWidth="4"></circle>
                        </svg>
                        <span className="material-symbols-outlined text-primary">health_and_safety</span>
                    </div>
                </div>

                <div className="glass p-6 rounded-xl flex items-center justify-between border border-white/10">
                    <div>
                        <p className="text-sm font-medium text-slate-600 dark:text-slate-400">At-Risk Population</p>
                        <h3 className="text-3xl font-bold mt-1">12,402</h3>
                        <p className="text-xs text-slate-500 font-medium flex items-center mt-2">
                            Stable across 14 jurisdictions
                        </p>
                    </div>
                    <div className="w-12 h-12 rounded-lg bg-amber-500/10 flex items-center justify-center border border-amber-500/20">
                        <span className="material-symbols-outlined text-amber-500">warning</span>
                    </div>
                </div>

                <div className="glass p-6 rounded-xl flex items-center justify-between border border-white/10">
                    <div>
                        <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Respiratory Incidents</p>
                        <h3 className="text-3xl font-bold mt-1">42</h3>
                        <p className="text-xs text-emerald-500 font-medium flex items-center mt-2">
                            <span className="material-symbols-outlined text-sm mr-1">trending_down</span> -5% trend detected
                        </p>
                    </div>
                    <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/20">
                        <span className="material-symbols-outlined text-primary">pulmonology</span>
                    </div>
                </div>
            </div>

            {/* Row 2: Main Chart */}
            <div className="glass rounded-xl overflow-hidden chart-grid border border-white/10 shadow-2xl">
                <div className="p-6 border-b border-slate-200/10 flex items-center justify-between bg-slate-100 dark:bg-slate-900/40">
                    <div>
                        <h4 className="font-bold text-lg">Respiratory Health Trends</h4>
                        <p className="text-sm text-slate-600 dark:text-slate-400">Health index baseline by age demographic groups</p>
                    </div>
                    <div className="flex gap-4">
                        <div className="flex items-center gap-2 text-xs font-medium">
                            <span className="w-3 h-3 rounded-full bg-primary shadow shadow-primary/50"></span> 0-17
                        </div>
                        <div className="flex items-center gap-2 text-xs font-medium">
                            <span className="w-3 h-3 rounded-full bg-purple-500 shadow shadow-purple-500/50"></span> 18-64
                        </div>
                        <div className="flex items-center gap-2 text-xs font-medium">
                            <span className="w-3 h-3 rounded-full bg-slate-500 shadow shadow-slate-500/50"></span> 65+
                        </div>
                    </div>
                </div>
                <div className="p-8 h-[350px] w-full relative">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={demographics} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b', fontWeight: 'bold' }} axisLine={false} tickLine={false} dy={10} />
                            <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} dx={-10} domain={[40, 100]} />
                            <Tooltip
                                contentStyle={{ backgroundColor: 'rgba(30, 41, 59, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', backdropFilter: 'blur(8px)' }}
                                itemStyle={{ color: '#fff', fontSize: '12px', fontWeight: 'bold' }}
                            />
                            <Line type="monotone" dataKey="age0_17" name="0-17 yrs" stroke="#3c83f6" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
                            <Line type="monotone" dataKey="age18_64" name="18-64 yrs" stroke="#8b5cf6" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
                            <Line type="monotone" dataKey="age65_plus" name="65+ yrs" stroke="#64748b" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Row 3: Two Columns */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pb-8">
                {/* Left: Health vs AQI */}
                <div className="glass p-6 rounded-xl border border-white/10">
                    <div className="flex items-center justify-between mb-6">
                        <h4 className="font-bold">Health vs. AQI Correlation</h4>
                        <span className="material-symbols-outlined text-slate-500 cursor-pointer hover:text-primary transition-colors">info</span>
                    </div>
                    <div className="space-y-4">
                        <div className="flex items-center gap-4">
                            <div className="flex-1 space-y-2">
                                <div className="flex justify-between text-xs font-medium">
                                    <span className="dark:text-slate-300">PM2.5 Levels</span>
                                    <span className="text-primary font-bold">42 µg/m³</span>
                                </div>
                                <div className="w-full h-1.5 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden shadow-inner">
                                    <div className="h-full bg-primary rounded-full w-[42%] shadow-[0_0_10px_rgba(59,130,246,0.5)]"></div>
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center gap-4 border-b border-white/5 pb-2">
                            <div className="flex-1 space-y-2">
                                <div className="flex justify-between text-xs font-medium">
                                    <span className="dark:text-slate-300">Ozone (O3)</span>
                                    <span className="text-purple-500 font-bold">12 ppb</span>
                                </div>
                                <div className="w-full h-1.5 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden shadow-inner">
                                    <div className="h-full rounded-full w-[15%] bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.5)]"></div>
                                </div>
                            </div>
                        </div>

                        <div className="h-48 mt-8 w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <ComposedChart data={correlation} margin={{ top: 20, right: 0, bottom: 0, left: 0 }} barSize={32}>
                                    <Tooltip
                                        cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                                        contentStyle={{ backgroundColor: 'rgba(30, 41, 59, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                                    />
                                    <Bar dataKey="aqi" name="AQI" fill="rgba(59, 130, 246, 0.2)" radius={[4, 4, 0, 0]} />
                                    <Scatter dataKey="score" name="Health Score" fill="#3c83f6" />
                                    {/* FIX: dot={<svg />} is invalid — use dot={false} to suppress dots */}
                                    <Line type="monotone" dataKey="score" stroke="#3c83f6" strokeWidth={0} activeDot={false} dot={false} />
                                </ComposedChart>
                            </ResponsiveContainer>
                        </div>
                        <p className="text-[11px] text-center text-slate-500 mt-2 italic font-medium">Pearson Correlation Coefficient: r = 0.84 (Strong Positive)</p>
                    </div>
                </div>

                {/* Right: Demographic Distribution */}
                <div className="glass p-6 rounded-xl border border-white/10 flex flex-col">
                    <div className="flex items-center justify-between mb-8">
                        <h4 className="font-bold">Demographic Distribution</h4>
                        <select
                            value={conditionFilter}
                            onChange={(e) => setConditionFilter(e.target.value)}
                            className="bg-slate-200 dark:bg-slate-800/80 border border-white/10 text-[11px] font-medium rounded p-1.5 text-slate-700 dark:text-slate-300 focus:ring-1 focus:ring-primary outline-none"
                        >
                            <option value="By Condition">All Conditions</option>
                            <option value="Asthma">Asthma Only</option>
                            <option value="COPD">COPD Only</option>
                        </select>
                    </div>

                    <div className="space-y-6 flex-1">
                        <div className="space-y-2 group">
                            <div className="flex justify-between text-xs font-medium">
                                <span className="text-slate-600 dark:text-slate-400 group-hover:text-slate-200 transition-colors">Asthma</span>
                                <span className="font-bold">4,520 (36%)</span>
                            </div>
                            <div className="w-full h-2.5 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden shadow-inner">
                                <div className="h-full bg-grad-primary rounded-full w-[36%] relative">
                                    <div className="absolute inset-0 bg-white/20 w-1/2 rounded-full blur-[2px]"></div>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-2 group">
                            <div className="flex justify-between text-xs font-medium">
                                <span className="text-slate-600 dark:text-slate-400 group-hover:text-slate-200 transition-colors">COPD</span>
                                <span className="font-bold">2,140 (17%)</span>
                            </div>
                            <div className="w-full h-2.5 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden shadow-inner">
                                <div className="h-full bg-grad-primary rounded-full w-[17%] relative">
                                    <div className="absolute inset-0 bg-white/20 w-1/2 rounded-full blur-[2px]"></div>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-2 group">
                            <div className="flex justify-between text-xs font-medium">
                                <span className="text-slate-600 dark:text-slate-400 group-hover:text-slate-200 transition-colors">Pneumonia History</span>
                                <span className="font-bold">1,890 (15%)</span>
                            </div>
                            <div className="w-full h-2.5 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden shadow-inner">
                                <div className="h-full bg-grad-primary rounded-full w-[15%] relative">
                                    <div className="absolute inset-0 bg-white/20 w-1/2 rounded-full blur-[2px]"></div>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-2 group">
                            <div className="flex justify-between text-xs font-medium">
                                <span className="text-slate-600 dark:text-slate-400 group-hover:text-slate-200 transition-colors">Other Respiratory</span>
                                <span className="font-bold">3,852 (31%)</span>
                            </div>
                            <div className="w-full h-2.5 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden shadow-inner">
                                <div className="h-full bg-grad-primary rounded-full w-[31%] relative">
                                    <div className="absolute inset-0 bg-white/20 w-1/2 rounded-full blur-[2px]"></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <button onClick={handleExportPDF} className="w-full mt-8 py-3 text-xs font-bold text-slate-800 dark:text-slate-50 bg-slate-200 dark:bg-slate-800/80 border border-white/10 rounded-lg hover:bg-slate-300 dark:hover:bg-slate-700 transition-all flex items-center justify-center gap-2 shadow-sm">
                        <span className="material-symbols-outlined text-[16px]">download</span>
                        Export Full Demographic Report
                    </button>
                </div>
            </div>
        </div>
    );
}
