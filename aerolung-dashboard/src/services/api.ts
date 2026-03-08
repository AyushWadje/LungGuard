const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// ==========================================
// Core Types
// ==========================================

export interface CityAQI {
    city: string;
    aqi: number;
}

export interface RiskPredictionRequest {
    aqi: number;
    spo2: number;
    age: number;
    smoker: boolean;
    asthma: boolean;
    heart_rate: number;
}

export interface RiskPredictionResponse {
    risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
    detailed_analysis?: Record<string, unknown>;
}

export interface DashboardStats {
    total_users: number;
    users_trend: string;
    avg_aqi: number;
    aqi_status: string;
    active_alerts: number;
    hospital_admissions: number;
    admissions_trend: string;
}

export interface HealthTrend {
    name: string;
    health: number;
    pollution: number;
}

export interface Pollutant {
    name: string;
    value: number;
    unit: string;
    fill: string;
}

export interface LiveSensor {
    id: string;
    lat: number;
    lng: number;
    aqi: number;
    pm25: number;
}

export interface RiskZone {
    id: string;
    name: string;
    severity: string;
    polygon: number[][];
}

export interface ActiveAlert {
    id: string;
    severity: string;
    title: string;
    location: string;
    population: number;
    color: string;
    status: string;
}

export interface HistoricalTrend {
    month: string;
    pm25: number;
    o3: number;
    no2: number;
    respiratory: number;
}

export interface YoYCorrelation {
    aqi: number;
    admissions: number;
}

export interface HealthDemographic {
    name: string;
    age0_17: number;
    age18_64: number;
    age65_plus: number;
}

export interface HealthCorrelation {
    name: string;
    aqi: number;
    score: number;
}

export interface UserProfile {
    name: string;
    role: string;
    email: string;
    avatar: string;
    avatar_url: string;
}

export interface WorkspaceSettings {
    name: string;
    timezone: string;
    primary_region: string;
}

export interface TeamMember {
    id: string;
    name: string;
    email: string;
    role: string;
}

// ==========================================
// Cities AQI
// ==========================================

export async function fetchCitiesAQI(): Promise<CityAQI[]> {
    try {
        const response = await fetch(`${API_BASE_URL}/cities-aqi`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Failed to fetch cities AQI:", error);
        return [
            { city: 'Mumbai', aqi: 112 },
            { city: 'Delhi', aqi: 245 },
            { city: 'Pune', aqi: 85 },
            { city: 'Bangalore', aqi: 42 },
            { city: 'Chennai', aqi: 65 },
            { city: 'Kolkata', aqi: 168 },
        ];
    }
}

// ==========================================
// Risk Prediction
// ==========================================

export async function predictRisk(data: RiskPredictionRequest): Promise<RiskPredictionResponse> {
    try {
        const queryParams = new URLSearchParams({
            aqi: data.aqi.toString(),
            spo2: data.spo2.toString(),
            age: data.age.toString(),
            smoker: data.smoker.toString(),
            asthma: data.asthma.toString(),
            heart_rate: data.heart_rate.toString(),
        });

        const response = await fetch(`${API_BASE_URL}/predict?${queryParams.toString()}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Failed to predict risk:", error);
        throw error;
    }
}

// ==========================================
// Dashboard Endpoints
// ==========================================

export async function fetchDashboardStats(): Promise<DashboardStats> {
    const response = await fetch(`${API_BASE_URL}/api/dashboard/stats`);
    if (!response.ok) throw new Error("Failed to fetch dashboard stats");
    return await response.json();
}

export async function fetchHealthTrends(): Promise<HealthTrend[]> {
    const response = await fetch(`${API_BASE_URL}/api/dashboard/health-trends`);
    if (!response.ok) throw new Error("Failed to fetch health trends");
    return await response.json();
}

export async function fetchPollutants(): Promise<Pollutant[]> {
    const response = await fetch(`${API_BASE_URL}/api/dashboard/pollutants`);
    if (!response.ok) throw new Error("Failed to fetch pollutants");
    return await response.json();
}

// ==========================================
// Population Health Endpoints
// ==========================================

export async function fetchHealthDemographics(condition?: string): Promise<HealthDemographic[]> {
    const params = condition ? `?condition=${encodeURIComponent(condition)}` : '';
    const response = await fetch(`${API_BASE_URL}/api/health/demographics${params}`);
    if (!response.ok) throw new Error("Failed to fetch health demographics");
    return await response.json();
}

export async function fetchHealthCorrelation(): Promise<HealthCorrelation[]> {
    const response = await fetch(`${API_BASE_URL}/api/health/correlation`);
    if (!response.ok) throw new Error("Failed to fetch health correlation");
    return await response.json();
}

// ==========================================
// Map Endpoints
// ==========================================

export async function fetchLiveSensors(): Promise<LiveSensor[]> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/map/sensors/live`);
        if (!response.ok) throw new Error("Failed to fetch live sensors");
        return await response.json();
    } catch (error) {
        console.error("Failed to fetch live sensors:", error);
        return [
            { id: "s1", lat: 40.7128, lng: -74.0060, aqi: 55, pm25: 12 },
            { id: "s2", lat: 40.7580, lng: -73.9855, aqi: 120, pm25: 45 },
        ];
    }
}

export async function fetchZones(): Promise<RiskZone[]> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/map/zones`);
        if (!response.ok) throw new Error("Failed to fetch risk zones");
        return await response.json();
    } catch (error) {
        console.error("Failed to fetch zones:", error);
        return [];
    }
}

// ==========================================
// Alerts Endpoints
// ==========================================

export async function fetchActiveAlerts(): Promise<ActiveAlert[]> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/alerts/active`);
        if (!response.ok) throw new Error("Failed to fetch active alerts");
        return await response.json();
    } catch (error) {
        console.error("Failed to fetch alerts:", error);
        return [];
    }
}

export async function acknowledgeAlert(id: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/alerts/${id}/acknowledge`, { method: 'POST' });
    if (!response.ok) throw new Error("Failed to acknowledge alert");
    return await response.json();
}

export async function issueAlertAdvisory(id: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/alerts/${id}/advisory`, { method: 'POST' });
    if (!response.ok) throw new Error("Failed to issue advisory");
    return await response.json();
}

// ==========================================
// Analytics Endpoints
// ==========================================

export async function fetchHistoricalAnalytics(range: string = '12m'): Promise<HistoricalTrend[]> {
    const response = await fetch(`${API_BASE_URL}/api/analytics/historical?range=${range}`);
    if (!response.ok) throw new Error("Failed to fetch historical analytics");
    return await response.json();
}

export async function fetchYoYAnalytics(): Promise<YoYCorrelation[]> {
    const response = await fetch(`${API_BASE_URL}/api/analytics/yoy`);
    if (!response.ok) throw new Error("Failed to fetch YoY analytics");
    return await response.json();
}

export async function exportAnalyticsReport(format: string = 'pdf'): Promise<{ status: string; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/analytics/export?format=${format}`);
    if (!response.ok) throw new Error("Failed to export analytics report");
    return await response.json();
}

// ==========================================
// User Profile & Workspace
// ==========================================

export async function fetchProfile(): Promise<UserProfile> {
    const response = await fetch(`${API_BASE_URL}/api/users/profile`);
    if (!response.ok) throw new Error("Failed to fetch profile");
    return await response.json();
}

export async function updateProfile(profile: UserProfile): Promise<{ message: string; data: UserProfile }> {
    const response = await fetch(`${API_BASE_URL}/api/users/profile`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
    });
    if (!response.ok) throw new Error("Failed to update profile");
    return await response.json();
}

export async function fetchWorkspace(): Promise<WorkspaceSettings> {
    const response = await fetch(`${API_BASE_URL}/api/workspaces/current`);
    if (!response.ok) throw new Error("Failed to fetch workspace");
    return await response.json();
}

export async function updateWorkspace(workspace: WorkspaceSettings): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/workspaces/current`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(workspace),
    });
    if (!response.ok) throw new Error("Failed to update workspace");
    return await response.json();
}

export async function updateNotifications(settings: Record<string, boolean>): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/users/notifications`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
    });
    if (!response.ok) throw new Error("Failed to update notifications");
    return await response.json();
}

// ==========================================
// Team Management
// ==========================================

export async function fetchTeamMembers(): Promise<TeamMember[]> {
    const response = await fetch(`${API_BASE_URL}/api/team/members`);
    if (!response.ok) throw new Error("Failed to fetch team members");
    return await response.json();
}

export async function inviteTeamMember(email: string, role: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/team/invite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, role }),
    });
    if (!response.ok) throw new Error("Failed to invite team member");
    return await response.json();
}

// ==========================================
// Authentication
// ==========================================

export async function login(email: string, password: string): Promise<{ access_token: string; token_type: string; expires_in: number; user: any }> {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
        throw new Error('Invalid credentials');
    }
    return response.json();
}

export async function logout(): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: 'POST',
    });

    if (!response.ok) {
        throw new Error('Logout failed');
    }
    return response.json();
}

export async function changePassword(old_password: string, new_password: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/auth/password/change`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ old_password, new_password }),
    });

    if (!response.ok) {
        throw new Error('Failed to change password');
    }
    return response.json();
}
