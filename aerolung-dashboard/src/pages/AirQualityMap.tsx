 import { useState, useEffect } from 'react';
import { fetchCitiesAQI, fetchLiveSensors, fetchZones, type CityAQI, type LiveSensor, type RiskZone } from '../services/api';

// Pre-define AQI status mappings with actual Tailwind classes (not dynamic)
const AQI_STATUS_MAP = {
    good: { dotClass: 'bg-emerald-500 shadow-emerald-500/80', text: 'Good' },
    moderate: { dotClass: 'bg-yellow-500 shadow-yellow-500/80', text: 'Moderate' },
    unhealthy: { dotClass: 'bg-orange-500 shadow-orange-500/80', text: 'Unhealthy' },
    hazardous: { dotClass: 'bg-red-500 shadow-red-500/80', text: 'Hazardous' },
} as const;

type AQIStatusKey = keyof typeof AQI_STATUS_MAP;

function getAQIStatusKey(aqi: number): AQIStatusKey {
    if (aqi <= 50) return 'good';
    if (aqi <= 100) return 'moderate';
    if (aqi <= 200) return 'unhealthy';
    return 'hazardous';
}

export default function AirQualityMap() {
    const [cities, setCities] = useState<CityAQI[]>([]);
    const [sensors, setSensors] = useState<LiveSensor[]>([]);
    const [zones, setZones] = useState<RiskZone[]>([]);
    const [loading, setLoading] = useState(true);
    // FIX: Active map layer state — clicking layer buttons now switches the active layer
    const [activeLayer, setActiveLayer] = useState<string>('PM2.5');
    // FIX: Search query state — filters the city list in the left panel
    const [searchQuery, setSearchQuery] = useState('');
    // FIX: Tooltip visibility state — close button now hides the overlay
    const [showTooltip, setShowTooltip] = useState(true);
    // FIX: Forecast play state — play button toggles animation
    const [isPlaying, setIsPlaying] = useState(false);
    // FIX: Zoom level state — zoom buttons now update the displayed level
    const [zoomLevel, setZoomLevel] = useState(10);

    useEffect(() => {
        async function loadData() {
            try {
                const [cityData, sensorData, zoneData] = await Promise.all([
                    fetchCitiesAQI(),
                    fetchLiveSensors(),
                    fetchZones(),
                ]);
                setCities(cityData);
                setSensors(sensorData);
                setZones(zoneData);
            } catch (err) {
                console.error("Error loading AQI data:", err);
            } finally {
                setLoading(false);
            }
        }
        loadData();
    }, []);

    return (
        <div className="relative flex-1 bg-slate-50 dark:bg-[#0b0f1a] overflow-hidden min-h-screen">
            {/* Map Placeholder */}
            <div className="absolute inset-0 z-0">
                <img className="w-full h-full object-cover opacity-60 mix-blend-screen grayscale brightness-75 contrast-125" alt="Dark stylized satellite map" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDSKpo0LjVwquEBWVs6LoeR-jM4UusHQjpSa5J0Sjb2QrUF6ygQGDlelrg571L53twWBA1YfiUi__wvGYcbCTn9orb40Na2guEPyCneIpwKQEYOjSmQHSYc7BLxQkfIiMXGEKCozVQeyI-6NgFnERbWo2hVNlka-2WJ3KQssBe_DLTTuKUghaQf2Sk_YP6L5ByFCKfGyG4QtxQrK55Cp3xiq2oNyWR-2AZfSxj-5XX8YZs0x_DF10sjoFXnJT-kFZd0O1lkD-hNoBg" />
                {/* Pulsing Hotspots (Map Markers simulated) */}
                {sensors.map((s, i) => (
                    <div key={s.id} className="absolute size-24 bg-red-600/30 rounded-full blur-2xl animate-pulse"
                        style={{ top: `${(i * 25 + 20)}%`, left: `${(i * 30 + 20)}%` }}></div>
                ))}
                {zones.map((z, i) => (
                    <div key={z.id} className="absolute size-40 bg-purple-600/20 rounded-full blur-3xl animate-pulse"
                        style={{ bottom: `${(i * 20 + 20)}%`, right: `${(i * 40 + 20)}%` }}></div>
                ))}
            </div>

            {/* Floating Left Panel: Stations */}
            <div className="absolute top-6 left-6 w-80 glass-panel rounded-xl shadow-2xl z-10 flex flex-col max-h-[calc(100vh-160px)]">
                <div className="p-4 border-b border-slate-300 dark:border-white/10">
                    <div className="relative mb-4">
                        <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-700 dark:text-slate-400 text-lg">search</span>
                        {/* FIX: Controlled search input — filters city list below */}
                        <input
                            className="w-full bg-slate-100 dark:bg-slate-900/50 border border-slate-300 dark:border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-primary"
                            placeholder="Search station or city..."
                            type="text"
                            value={searchQuery}
                            onChange={e => setSearchQuery(e.target.value)}
                        />
                    </div>
                    <h3 className="text-slate-900 dark:text-white font-semibold text-sm">Active Monitoring Stations</h3>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
                    {loading ? (
                        <div className="p-4 text-center text-slate-400 text-sm">Fetching live data from backend...</div>
                    ) : (
                        // FIX: Filter cities by searchQuery
                        cities.filter(c => c.city.toLowerCase().includes(searchQuery.toLowerCase())).map((cityData, index) => {
                            const statusKey = getAQIStatusKey(cityData.aqi);
                            const status = AQI_STATUS_MAP[statusKey];
                            return (
                                <div key={index} className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-200 dark:hover:bg-white/5 cursor-pointer border border-transparent hover:border-slate-300 dark:hover:border-white/10 group">
                                    <div className="flex items-center gap-3">
                                        <div className={`size-2 rounded-full ${status.dotClass}`}></div>
                                        <div>
                                            <p className="text-sm font-medium text-slate-900 dark:text-white">{cityData.city}</p>
                                            <p className="text-xs text-slate-700 dark:text-slate-400">AQI: {cityData.aqi} • {status.text}</p>
                                        </div>
                                    </div>
                                    <span className="material-symbols-outlined text-slate-600 dark:text-slate-500 group-hover:text-primary">chevron_right</span>
                                </div>
                            );
                        })
                    )}
                </div>
            </div>

            {/* Floating Right Panel: Layers & Legend */}
            <div className="absolute top-6 right-6 w-64 flex flex-col gap-4 z-10">
                {/* Map Layers */}
                <div className="glass-panel rounded-xl p-4 shadow-xl">
                    <h3 className="text-slate-900 dark:text-white text-xs font-bold uppercase tracking-wider mb-4 opacity-70">Map Layers</h3>
                    {/* FIX: Layer buttons now use activeLayer state — clicking switches the active layer */}
                    <div className="grid grid-cols-1 gap-2">
                        {(['PM2.5', 'PM10', 'O3', 'NO2', 'SO2'] as const).map(layer => (
                            <button
                                key={layer}
                                onClick={() => setActiveLayer(layer)}
                                className={`flex items-center justify-between p-2 rounded-lg text-xs font-semibold transition-colors ${
                                    activeLayer === layer
                                        ? 'bg-primary text-white'
                                        : 'bg-slate-200 dark:bg-white/5 text-slate-600 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-white/10 font-medium'
                                }`}
                            >
                                <span>
                                    {layer === 'PM2.5' ? 'PM2.5 (Fine Matter)' :
                                     layer === 'PM10' ? 'PM10 (Inhalable)' :
                                     layer === 'O3' ? 'O3 (Ozone)' :
                                     layer === 'NO2' ? 'NO2 (Nitrogen Dioxide)' :
                                     'SO2 (Sulfur Dioxide)'}
                                </span>
                                {activeLayer === layer && (
                                    <span className="material-symbols-outlined text-sm">check_circle</span>
                                )}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Legend */}
                <div className="glass-panel rounded-xl p-4 shadow-xl">
                    <h3 className="text-slate-900 dark:text-white text-xs font-bold uppercase tracking-wider mb-3 opacity-70">AQI Index</h3>
                    <div className="h-2 w-full aqi-gradient rounded-full mb-3"></div>
                    <div className="space-y-2">
                        <div className="flex items-center justify-between text-[10px] uppercase font-bold text-slate-700 dark:text-slate-400">
                            <span>Good</span>
                            <span className="text-emerald-400">0 - 50</span>
                        </div>
                        <div className="flex items-center justify-between text-[10px] uppercase font-bold text-slate-700 dark:text-slate-400">
                            <span>Moderate</span>
                            <span className="text-yellow-400">51 - 100</span>
                        </div>
                        <div className="flex items-center justify-between text-[10px] uppercase font-bold text-slate-700 dark:text-slate-400">
                            <span>Unhealthy</span>
                            <span className="text-orange-500">101 - 200</span>
                        </div>
                        <div className="flex items-center justify-between text-[10px] uppercase font-bold text-slate-700 dark:text-slate-400">
                            <span>Hazardous</span>
                            <span className="text-red-500">201+</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* FIX: Zoom Controls — buttons now update zoomLevel state */}
            <div className="absolute bottom-32 right-6 flex flex-col gap-2 z-10">
                <button
                    onClick={() => setZoomLevel(z => Math.min(z + 1, 20))}
                    className="size-10 glass-panel rounded-lg flex items-center justify-center text-slate-900 dark:text-white hover:bg-primary hover:text-white transition-colors"
                    title={`Zoom in (level ${zoomLevel})`}
                >
                    <span className="material-symbols-outlined">add</span>
                </button>
                <button
                    onClick={() => setZoomLevel(z => Math.max(z - 1, 1))}
                    className="size-10 glass-panel rounded-lg flex items-center justify-center text-slate-900 dark:text-white hover:bg-primary hover:text-white transition-colors"
                    title={`Zoom out (level ${zoomLevel})`}
                >
                    <span className="material-symbols-outlined">remove</span>
                </button>
                <div className="size-10 glass-panel rounded-lg flex items-center justify-center text-[9px] font-bold text-primary">
                    {zoomLevel}x
                </div>
                <button
                    onClick={() => setZoomLevel(10)}
                    className="size-10 glass-panel rounded-lg flex items-center justify-center text-slate-900 dark:text-white hover:bg-primary hover:text-white transition-colors mt-1"
                    title="Reset to current location"
                >
                    <span className="material-symbols-outlined">near_me</span>
                </button>
            </div>

            {/* Bottom Panel: Timeline/Forecast Slider */}
            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-[calc(100%-400px)] glass-panel rounded-2xl p-6 shadow-2xl z-10 border-t border-white/20">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-4">
                        {/* FIX: Play button now toggles isPlaying state */}
                        <button
                            onClick={() => setIsPlaying(p => !p)}
                            className={`size-8 rounded-full flex items-center justify-center text-white transition-colors ${isPlaying ? 'bg-amber-500' : 'bg-primary'}`}
                        >
                            <span className="material-symbols-outlined text-sm">{isPlaying ? 'pause' : 'play_arrow'}</span>
                        </button>
                        <div>
                            <h4 className="text-slate-900 dark:text-white text-sm font-semibold leading-none">24-Hour Forecast</h4>
                            <p className="text-xs text-slate-700 dark:text-slate-400 mt-1">Showing PM2.5 projections for Next 24 Hours</p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <span className="px-2 py-1 rounded bg-slate-200 dark:bg-white/5 text-[10px] font-bold text-slate-600 dark:text-slate-300">NOW: 14:00</span>
                        <span className="px-2 py-1 rounded bg-primary/20 text-[10px] font-bold text-primary">PROJECTED: 22:00</span>
                    </div>
                </div>

                <div className="relative pt-2">
                    <div className="h-1 w-full bg-slate-300 dark:bg-white/10 rounded-full relative">
                        <div className="absolute left-0 top-0 h-1 w-[60%] bg-primary rounded-full"></div>
                        <div className="absolute top-1/2 left-0 -translate-y-1/2 w-full flex justify-between px-1">
                            <div className="size-2 rounded-full bg-slate-500"></div>
                            <div className="size-2 rounded-full bg-slate-500"></div>
                            <div className="size-2 rounded-full bg-slate-500"></div>
                            <div className="size-2 rounded-full bg-slate-500"></div>
                            <div className="size-2 rounded-full bg-slate-500"></div>
                            <div className="size-2 rounded-full bg-slate-500"></div>
                        </div>
                        <div className="absolute left-[60%] top-1/2 -translate-y-1/2 size-4 bg-primary border-2 border-white rounded-full shadow-[0_0_15px_rgba(60,131,246,0.6)] cursor-grab active:cursor-grabbing"></div>
                    </div>

                    <div className="flex justify-between mt-4 text-[10px] font-medium text-slate-600 dark:text-slate-500 uppercase tracking-tighter">
                        <span>08:00</span>
                        <span>12:00</span>
                        <span className="text-primary font-bold">16:00</span>
                        <span>20:00</span>
                        <span>00:00</span>
                        <span>04:00</span>
                        <span>08:00</span>
                    </div>
                </div>
            </div>

            {/* FIX: Station Tooltip Overlay — close button hides it, "STATION DETAILS" shows expanded info */}
            {showTooltip && (
                <div className="absolute top-[45%] left-[52%] glass-panel p-4 rounded-xl shadow-2xl z-20 w-48 border border-primary/40">
                    <div className="flex justify-between items-start mb-2">
                        <span className="text-[10px] font-bold bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded">EXCELLENT</span>
                        {/* FIX: Close button now hides the tooltip */}
                        <button onClick={() => setShowTooltip(false)} className="text-slate-700 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors">
                            <span className="material-symbols-outlined text-sm">close</span>
                        </button>
                    </div>
                    <p className="text-xs font-bold text-slate-900 dark:text-white mb-1">Oakland Tech Hub</p>
                    <div className="flex items-baseline gap-1">
                        <span className="text-2xl font-black text-slate-900 dark:text-white">12</span>
                        <span className="text-[10px] text-slate-700 dark:text-slate-400 uppercase">AQI</span>
                    </div>
                    <div className="mt-2 space-y-1 text-[10px] text-slate-600 dark:text-slate-400">
                        <div className="flex justify-between">
                            <span>Active Layer:</span>
                            <span className="font-bold text-primary">{activeLayer}</span>
                        </div>
                        <div className="flex justify-between">
                            <span>Zoom Level:</span>
                            <span className="font-bold text-slate-700 dark:text-slate-300">{zoomLevel}x</span>
                        </div>
                    </div>
                    {/* FIX: "STATION DETAILS" button now shows a brief details expansion */}
                    <button
                        onClick={() => alert('Station: Oakland Tech Hub\nCoords: 37.8044° N, 122.2712° W\nPM2.5: 4.2 µg/m³\nO3: 18 ppb\nStatus: Excellent')}
                        className="w-full mt-3 py-1.5 bg-primary/20 hover:bg-primary/30 text-primary text-[10px] font-bold rounded-lg transition-colors"
                    >
                        STATION DETAILS
                    </button>
                    <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 size-4 glass-panel rotate-45 border-t-0 border-l-0"></div>
                </div>
            )}
            {/* Re-open tooltip button when closed */}
            {!showTooltip && (
                <button
                    onClick={() => setShowTooltip(true)}
                    className="absolute top-[45%] left-[52%] z-20 size-8 bg-primary rounded-full flex items-center justify-center text-white shadow-lg shadow-primary/40 hover:bg-primary/90 transition-colors"
                    title="Show station info"
                >
                    <span className="material-symbols-outlined text-sm">info</span>
                </button>
            )}
        </div>
    );
}
