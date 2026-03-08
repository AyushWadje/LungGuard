import { useState, useEffect, useRef } from 'react';
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';
import { AreaChart, Area, ResponsiveContainer, ComposedChart, Line, XAxis, Tooltip, ScatterChart, Scatter, CartesianGrid, YAxis } from 'recharts';
import { fetchHistoricalAnalytics, fetchYoYAnalytics, type HistoricalTrend, type YoYCorrelation } from '../services/api';

const miniTrend1 = [
    { value: 65 }, { value: 78 }, { value: 72 }, { value: 85 }, { value: 70 }, { value: 92 }, { value: 88 }
];

const miniTrend2 = [
    { value: 45 }, { value: 38 }, { value: 42 }, { value: 25 }, { value: 30 }, { value: 22 }, { value: 20 }
];

export default function Analytics() {
    const [historicalData, setHistoricalData] = useState<HistoricalTrend[]>([]);
    const [yoyData, setYoyData] = useState<YoYCorrelation[]>([]);
    const [timeRange, setTimeRange] = useState('12m');
    const [exporting, setExporting] = useState(false);
    const chartRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const loadAnalytics = async () => {
            try {
                const [histData, scatterData] = await Promise.all([
                    fetchHistoricalAnalytics(timeRange),
                    fetchYoYAnalytics()
                ]);
                setHistoricalData(histData);
                setYoyData(scatterData);
            } catch (error) {
                console.error("Failed to load analytics endpoints", error);
            }
        };
        loadAnalytics();
        const interval = setInterval(loadAnalytics, 60000); // refresh every minute
        return () => clearInterval(interval);
    }, [timeRange]);

    const [exportError, setExportError] = useState<string | null>(null);
    // FIX: Controlled state for "Respiratory Overlay" toggle (was uncontrolled defaultChecked)
    const [showRespiratoryOverlay, setShowRespiratoryOverlay] = useState(true);

    const handleExport = async () => {
        if (!chartRef.current) return;
        setExportError(null);
        // FIX: setExporting(true) must be BEFORE the try block so the loading
        // state is always set even if html2canvas throws synchronously
        setExporting(true);
        try {
            const canvas = await html2canvas(chartRef.current, { scale: 2, useCORS: true, backgroundColor: '#0f172a' });
            const imgData = canvas.toDataURL('image/png');
            const pdf = new jsPDF('landscape', 'mm', 'a4');
            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
            pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
            pdf.save(`AeroLung_Analytics_${new Date().toISOString().split('T')[0]}.pdf`);
        } catch (error) {
            console.error("Export failed", error);
            setExportError("Failed to export report. Please try again.");
        } finally {
            setExporting(false);
        }
    };

    return (
        <div ref={chartRef} className="p-8 space-y-8">
            {exportError && (
                <div className="flex items-center gap-3 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                    <span className="material-symbols-outlined text-sm">error</span>
                    {exportError}
                    <button onClick={() => setExportError(null)} className="ml-auto text-red-400 hover:text-red-300">
                        <span className="material-symbols-outlined text-sm">close</span>
                    </button>
                </div>
            )}
            {/* Content Header */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                <div>
                    <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">Historical Health &amp; Air Analytics</h2>
                    <p className="text-slate-500 mt-1">Cross-referencing environmental pollutants with respiratory health outcomes.</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="bg-white/5 p-1 rounded-lg flex border border-white/10 shadow-sm">
                        <button onClick={() => setTimeRange('12m')} className={`px-4 py-1.5 text-sm font-semibold rounded-md shadow-sm transition-colors ${timeRange === '12m' ? 'bg-grad-primary text-slate-50 dark:text-white' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'}`}>Last 12 Months</button>
                        <button onClick={() => setTimeRange('ytd')} className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${timeRange === 'ytd' ? 'bg-grad-primary text-slate-50 dark:text-white shadow-sm' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'}`}>YTD</button>
                        {/* FIX: "Custom" shows a tooltip note — no backend support for arbitrary date ranges */}
                        <button
                            onClick={() => setTimeRange('custom')}
                            title="Custom date range: showing full 12-month dataset"
                            className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${timeRange === 'custom' ? 'bg-grad-primary text-slate-50 dark:text-white shadow-sm' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'}`}
                        >
                            Custom
                        </button>
                    </div>
                    <button
                        onClick={handleExport}
                        disabled={exporting}
                        className="flex items-center gap-2 px-6 py-2.5 bg-grad-primary text-slate-50 dark:text-white rounded-lg font-bold text-sm shadow-lg shadow-primary/20 hover:opacity-90 transition-all disabled:opacity-50"
                    >
                        <span className="material-symbols-outlined text-lg">{exporting ? 'hourglass_empty' : 'download'}</span>
                        {exporting ? 'Generating PDF...' : 'Export Report'}
                    </button>
                </div>
            </div>

            {/* Comparison Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Card 1 */}
                <div className="glass-card p-6 rounded-xl border border-white/10 flex flex-col justify-between h-40 relative overflow-hidden">
                    <div>
                        <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">Avg AQI</p>
                        <div className="flex items-baseline gap-2 mt-1">
                            <h3 className="text-3xl font-bold text-slate-900 dark:text-white">72.4</h3>
                            <span className="text-green-500 text-sm font-semibold flex items-center">
                                <span className="material-symbols-outlined text-sm">trending_down</span> 12%
                            </span>
                        </div>
                    </div>
                    <div className="h-12 w-full mt-4 flex items-end gap-1">
                        {[40, 60, 30, 80, 50, 45, 65].map((h, i) => (
                            <div key={i} className={`flex-1 rounded-t-sm ${i === 6 ? 'bg-grad-primary' : i >= 4 ? 'bg-primary/50' : 'bg-slate-200 dark:bg-slate-700/30'}`} style={{ height: `${h}%` }}></div>
                        ))}
                    </div>
                </div>

                {/* Card 2 */}
                <div className="glass-card p-6 rounded-xl border border-white/10 flex flex-col justify-between h-40 relative overflow-hidden">
                    <div>
                        <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">Health Index</p>
                        <div className="flex items-baseline gap-2 mt-1">
                            <h3 className="text-3xl font-bold text-slate-900 dark:text-white">88%</h3>
                            <span className="text-green-500 text-sm font-semibold flex items-center">
                                <span className="material-symbols-outlined text-sm">trending_up</span> 5%
                            </span>
                        </div>
                    </div>
                    <div className="h-12 w-full mt-4 absolute bottom-0 left-0 right-0">
                        <ResponsiveContainer width="100%" height={48}>
                            <AreaChart data={miniTrend1}>
                                <defs>
                                    <linearGradient id="miniColor1" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <Area type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#miniColor1)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Card 3 */}
                <div className="glass-card p-6 rounded-xl border border-white/10 flex flex-col justify-between h-40 relative overflow-hidden">
                    <div>
                        <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">Critical Alerts</p>
                        <div className="flex items-baseline gap-2 mt-1">
                            <h3 className="text-3xl font-bold text-slate-900 dark:text-white">14</h3>
                            <span className="text-green-500 text-sm font-semibold flex items-center">
                                <span className="material-symbols-outlined text-sm">trending_down</span> 8%
                            </span>
                        </div>
                    </div>
                    <div className="h-12 w-full mt-4 flex items-end gap-1">
                        {[70, 90, 50, 30, 40, 35, 20].map((h, i) => (
                            <div key={i} className={`flex-1 rounded-t-sm ${i === 6 ? 'bg-purple-500' : i >= 4 ? 'bg-purple-500/50' : 'bg-slate-200 dark:bg-slate-700/30'}`} style={{ height: `${h}%` }}></div>
                        ))}
                    </div>
                </div>

                {/* Card 4 */}
                <div className="glass-card p-6 rounded-xl border border-white/10 flex flex-col justify-between h-40 relative overflow-hidden">
                    <div>
                        <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">Avg Recovery Time</p>
                        <div className="flex items-baseline gap-2 mt-1">
                            <h3 className="text-3xl font-bold text-slate-900 dark:text-white">4.2d</h3>
                            <span className="text-green-500 text-sm font-semibold flex items-center">
                                <span className="material-symbols-outlined text-sm">trending_down</span> 15%
                            </span>
                        </div>
                    </div>
                    <div className="h-12 w-full mt-4 absolute bottom-0 left-0 right-0">
                        <ResponsiveContainer width="100%" height={48}>
                            <AreaChart data={miniTrend2}>
                                <defs>
                                    <linearGradient id="miniColor2" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <Area type="monotone" dataKey="value" stroke="#22c55e" strokeWidth={2} fillOpacity={1} fill="url(#miniColor2)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Main Chart Area */}
            <div className="glass-card p-8 rounded-xl border border-white/10">
                <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
                    <div>
                        <h4 className="text-xl font-bold text-slate-900 dark:text-white">Annual Pollutant Trends</h4>
                        <p className="text-sm text-slate-500">Monthly breakdown of key environmental indicators</p>
                    </div>
                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-4">
                            {/* FIX: Controlled toggle — showRespiratoryOverlay drives the Line visibility */}
                            <label className="inline-flex items-center cursor-pointer">
                                <input
                                    checked={showRespiratoryOverlay}
                                    onChange={e => setShowRespiratoryOverlay(e.target.checked)}
                                    className="sr-only peer"
                                    type="checkbox"
                                />
                                <div className="relative w-11 h-6 bg-slate-200 dark:bg-slate-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary/50 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                                <span className="ms-3 text-sm font-medium text-slate-300">Respiratory Overlay</span>
                            </label>
                        </div>
                        <div className="flex gap-4">
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full bg-blue-500 shadow shadow-blue-500/50"></span>
                                <span className="text-xs font-medium text-slate-600 dark:text-slate-400 uppercase">PM2.5</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full bg-purple-500 shadow shadow-purple-500/50"></span>
                                <span className="text-xs font-medium text-slate-600 dark:text-slate-400 uppercase">O3</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="relative h-[400px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={historicalData} margin={{ top: 20, right: 0, left: -20, bottom: 0 }}>
                            <defs>
                                <linearGradient id="area-grad" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="area-grad2" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.4} />
                                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="month" tick={{ fontSize: 10, fill: '#64748b', fontWeight: 'bold' }} axisLine={true} stroke="rgba(255,255,255,0.1)" tickLine={false} dy={10} />
                            <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} dx={-10} />
                            <Tooltip
                                contentStyle={{ backgroundColor: 'rgba(30, 41, 59, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', backdropFilter: 'blur(8px)' }}
                                itemStyle={{ color: '#fff', fontSize: '12px', fontWeight: 'bold' }}
                            />
                            <Area type="monotone" dataKey="pm25" name="PM2.5" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#area-grad)" />
                            <Area type="monotone" dataKey="o3" name="Ozone" stroke="#a855f7" strokeWidth={3} fillOpacity={1} fill="url(#area-grad2)" />
                            {/* FIX: Conditionally render based on controlled toggle state */}
                            {showRespiratoryOverlay && (
                                <Line type="monotone" dataKey="respiratory" name="Respiratory Cases" stroke="#22c55e" strokeWidth={2} strokeDasharray="5 5" dot={false} activeDot={{ r: 6 }} />
                            )}
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Bottom Row */}
            <div className="grid grid-cols-1 lg:grid-cols-10 gap-6 pb-8">
                {/* Correlation Analysis */}
                <div className="lg:col-span-6 glass-card p-8 rounded-xl border border-white/10">
                    <div className="flex items-center justify-between mb-6">
                        <h4 className="text-lg font-bold text-slate-900 dark:text-white">Historical Correlation Analysis</h4>
                        <span className="text-xs font-medium bg-slate-800 text-slate-600 dark:text-slate-400 px-2.5 py-1 rounded-full border border-slate-700 shadow-inner">AQI vs. Hospital Admissions</span>
                    </div>
                    <div className="h-64 relative bg-slate-900/40 rounded-lg border border-slate-800/80 overflow-hidden text-slate-50 dark:text-white shadow-inner">
                        <ResponsiveContainer width="100%" height="100%">
                            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: -10 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                <XAxis type="number" dataKey="aqi" name="AQI" stroke="#64748b" tick={{ fontSize: 10 }} tickLine={false} domain={[0, 200]} />
                                <YAxis type="number" dataKey="admissions" name="Admissions" stroke="#64748b" tick={{ fontSize: 10 }} tickLine={false} />
                                <Tooltip
                                    cursor={{ strokeDasharray: '3 3', stroke: 'rgba(255,255,255,0.2)' }}
                                    contentStyle={{ backgroundColor: 'rgba(30, 41, 59, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                                    itemStyle={{ color: '#fff', fontSize: '12px' }}
                                />
                                <Scatter name="Correlation" data={yoyData} fill="#3b82f6" />
                            </ScatterChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Year-over-Year */}
                <div className="lg:col-span-4 glass-card p-8 rounded-xl border border-white/10 flex flex-col justify-between">
                    <h4 className="text-lg font-bold mb-6 text-slate-900 dark:text-white">Year-over-Year Distribution</h4>
                    <div className="space-y-6">
                        <div className="space-y-2">
                            <div className="flex justify-between text-xs text-slate-600 dark:text-slate-400 font-medium">
                                <span>Particulates (PM2.5)</span>
                                <span>2024 vs 2025</span>
                            </div>
                            <div className="flex gap-1 h-3 group cursor-pointer hover:opacity-80 transition-opacity">
                                <div className="w-[45%] bg-slate-200 dark:bg-slate-700 rounded-l-full group-hover:bg-slate-600 transition-colors"></div>
                                <div className="w-4 h-3 rounded bg-grad-primary shadow-[0_0_10px_rgba(59,130,246,0.5)] group-hover:scale-110 transition-transform origin-left"></div>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex justify-between text-xs text-slate-600 dark:text-slate-400 font-medium">
                                <span>Ozone (O3)</span>
                                <span>2024 vs 2025</span>
                            </div>
                            <div className="flex gap-1 h-3 group cursor-pointer hover:opacity-80 transition-opacity">
                                <div className="w-[30%] bg-slate-200 dark:bg-slate-700 rounded-l-full group-hover:bg-slate-600 transition-colors"></div>
                                <div className="w-4 h-3 rounded bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.5)] group-hover:scale-110 transition-transform origin-left"></div>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex justify-between text-xs text-slate-600 dark:text-slate-400 font-medium">
                                <span>Nitrogen Dioxide (NO2)</span>
                                <span>2024 vs 2025</span>
                            </div>
                            <div className="flex gap-1 h-3 group cursor-pointer hover:opacity-80 transition-opacity">
                                <div className="w-[60%] bg-slate-200 dark:bg-slate-700 rounded-l-full group-hover:bg-slate-600 transition-colors"></div>
                                <div className="w-4 h-3 rounded bg-grad-primary shadow-[0_0_10px_rgba(59,130,246,0.5)] group-hover:scale-110 transition-transform origin-left"></div>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex justify-between text-xs text-slate-600 dark:text-slate-400 font-medium">
                                <span>Carbon Monoxide (CO)</span>
                                <span>2024 vs 2025</span>
                            </div>
                            <div className="flex gap-1 h-3 group cursor-pointer hover:opacity-80 transition-opacity">
                                <div className="w-[25%] bg-slate-200 dark:bg-slate-700 rounded-l-full group-hover:bg-slate-600 transition-colors"></div>
                                <div className="w-4 h-3 rounded bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.5)] group-hover:scale-110 transition-transform origin-left"></div>
                            </div>
                        </div>

                        <div className="flex items-center gap-6 pt-6 border-t border-white/10 mt-4">
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-sm bg-slate-200 dark:bg-slate-700"></span>
                                <span className="text-[10px] text-slate-600 dark:text-slate-400 font-bold uppercase tracking-widest">FY 2024</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-sm bg-grad-primary"></span>
                                <span className="text-[10px] text-slate-600 dark:text-slate-400 font-bold uppercase tracking-widest">FY 2025</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
