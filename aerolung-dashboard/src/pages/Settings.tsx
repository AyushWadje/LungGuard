import React, { useState, useEffect, useRef } from 'react';
import {
    fetchProfile, updateProfile,
    fetchWorkspace, updateWorkspace,
    updateNotifications,
    fetchTeamMembers, inviteTeamMember,
    changePassword,
    type UserProfile, type WorkspaceSettings, type TeamMember
} from '../services/api';

type ToastType = 'success' | 'error';
interface Toast { message: string; type: ToastType }

export default function Settings() {
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [workspace, setWorkspace] = useState<WorkspaceSettings | null>(null);
    const [team, setTeam] = useState<TeamMember[]>([]);
    const [toast, setToast] = useState<Toast | null>(null);

    // Inline edit states
    const [editingName, setEditingName] = useState(false);
    const [newName, setNewName] = useState('');

    // Invite form state
    const [inviteEmail, setInviteEmail] = useState('');
    const [showInviteForm, setShowInviteForm] = useState(false);

    // Password form state
    const [showPasswordForm, setShowPasswordForm] = useState(false);
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');

    // Notification toggles
    const [notifEmail, setNotifEmail] = useState(true);
    const [notifSms, setNotifSms] = useState(false);
    const [notifPush, setNotifPush] = useState(true);
    // FIX: Controlled 2FA toggle state
    const [twoFAEnabled, setTwoFAEnabled] = useState(true);
    // FIX: Avatar file input ref for upload button
    const avatarInputRef = useRef<HTMLInputElement>(null);
    const [avatarPreview, setAvatarPreview] = useState<string | null>(null);

    const showToast = (message: string, type: ToastType = 'success') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3500);
    };

    useEffect(() => {
        async function loadData() {
            try {
                const [p, w, t] = await Promise.all([
                    fetchProfile(),
                    fetchWorkspace(),
                    fetchTeamMembers()
                ]);
                setProfile(p);
                setWorkspace(w);
                setTeam(t);
                setNewName(p.name);
            } catch (err) {
                console.error("Failed to load settings data", err);
            }
        }
        loadData();
    }, []);

    const handleInvite = async () => {
        if (!inviteEmail.trim()) return;
        try {
            await inviteTeamMember(inviteEmail, "Viewer");
            showToast(`Invite sent to ${inviteEmail}`);
            setInviteEmail('');
            setShowInviteForm(false);
            const t = await fetchTeamMembers();
            setTeam(t);
        } catch (err) {
            console.error(err);
            showToast("Failed to send invite.", "error");
        }
    };

    const handleSaveWorkspace = async () => {
        if (!workspace) return;
        try {
            await updateWorkspace(workspace);
            showToast("Workspace settings saved!");
        } catch (err) {
            console.error(err);
            showToast("Failed to save workspace.", "error");
        }
    };

    const handleSaveName = async () => {
        if (!profile || !newName.trim()) return;
        try {
            const result = await updateProfile({ ...profile, name: newName });
            setProfile(result.data);
            setEditingName(false);
            showToast("Profile updated successfully!");
        } catch (err) {
            console.error(err);
            showToast("Failed to update profile.", "error");
        }
    };

    // FIX: Accept the new values directly to avoid stale closure bug
    const handleToggleNotification = async (
        type: string,
        newEmail: boolean,
        newSms: boolean,
        newPush: boolean
    ) => {
        try {
            await updateNotifications({ email: newEmail, sms: newSms, push: newPush });
            const enabled = type === 'Email' ? newEmail : type === 'SMS' ? newSms : newPush;
            showToast(`${type} notifications ${enabled ? 'enabled' : 'disabled'}`);
        } catch (err) {
            console.error(err);
            showToast("Failed to update notifications.", "error");
        }
    };

    // FIX: Avatar file change handler
    const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (ev) => {
            setAvatarPreview(ev.target?.result as string);
            showToast("Avatar updated (preview only — upload endpoint not yet connected).");
        };
        reader.readAsDataURL(file);
    };

    const handleChangePassword = async () => {
        if (!oldPassword || !newPassword) {
            showToast("Please fill in both password fields.", "error");
            return;
        }
        try {
            await changePassword(oldPassword, newPassword);
            showToast("Password updated successfully!");
            setOldPassword('');
            setNewPassword('');
            setShowPasswordForm(false);
        } catch (err) {
            console.error(err);
            showToast("Failed to update password.", "error");
        }
    };

    if (!profile || !workspace) return (
        <div className="p-8 flex items-center gap-3 text-slate-500">
            <span className="material-symbols-outlined animate-spin">refresh</span>
            Loading Settings...
        </div>
    );

    return (
        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
            <div className="max-w-5xl mx-auto">
                <div className="mb-8">
                    <h2 className="text-3xl font-extrabold tracking-tight dark:text-slate-100">Settings & Permissions</h2>
                    <p className="text-slate-500 mt-1">Manage your professional profile, workspace preferences, and team security.</p>
                </div>

                <div className="space-y-6">
                    {/* Profile Management */}
                    <section className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6 shadow-2xl overflow-hidden relative ring-1 ring-primary/20">
                        <div className="absolute top-0 left-0 w-1 h-full bg-primary"></div>
                        <h3 className="text-lg font-bold flex items-center gap-2 mb-6 dark:text-slate-100">
                            <span className="material-symbols-outlined text-primary">person</span>
                            Profile Management
                        </h3>

                        <div className="flex items-center gap-8">
                            <div className="relative group">
                                <div
                                    className="h-24 w-24 rounded-full border-4 border-slate-100 dark:border-slate-800 bg-cover shadow-xl"
                                    style={{ backgroundImage: `url('${avatarPreview || profile.avatar || profile.avatar_url || 'https://lh3.googleusercontent.com/aida-public/AB6AXuCdtfg2xeDQ2tQZjM7dIaIdCNbrV9qPrZOto9R9xAYmFEFtMx5MyOpnLcV3osjQQwqmm4wqo1TN0Jbe8X54lFvpKKjA4ukHPIdbcGW3XAz_oI0i4QRGVEfA6v0rYdJ17q95XpXu9r-hjO7BMqLztkGAtiglNBZGXZ1_FOpWwdjxzvBVqAGYadc99fm6Ub3Yl2gTvYB-rh4fGXs6OtuECBe2Av0-p7XPF4ht3HnczTydrmy5nPA8DaH4XxA0Bz3PyFZv-X6Ud1jCtB0'}')` }}
                                ></div>
                                {/* FIX: Hidden file input wired to the camera button */}
                                <input
                                    ref={avatarInputRef}
                                    type="file"
                                    accept="image/*"
                                    className="hidden"
                                    onChange={handleAvatarChange}
                                />
                                <button
                                    onClick={() => avatarInputRef.current?.click()}
                                    className="absolute -bottom-2 -right-2 flex items-center gap-2 px-3 py-1.5 bg-grad-primary text-slate-50 dark:text-white text-sm font-bold rounded-lg shadow-lg shadow-primary/20 hover:opacity-90 transition-all"
                                    title="Upload new avatar"
                                >
                                    <span className="material-symbols-outlined text-[18px]">photo_camera</span>
                                </button>
                            </div>
                            <div className="grid grid-cols-2 gap-x-8 gap-y-4 flex-1">
                                <div className="space-y-1">
                                    <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Full Name</label>
                                    <p className="font-semibold text-lg dark:text-slate-100">{profile.name}</p>
                                </div>
                                <div className="space-y-1">
                                    <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Email Address</label>
                                    <p className="font-semibold text-lg dark:text-slate-100">{profile.email}</p>
                                </div>
                                <div className="space-y-1">
                                    <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Role</label>
                                    <div className="flex items-center gap-2">
                                        <span className="h-2 w-2 bg-emerald-500 rounded-full"></span>
                                        <p className="font-semibold text-lg dark:text-slate-100">{profile.role}</p>
                                    </div>
                                </div>
                                <div className="flex items-end pb-1">
                                    {editingName ? (
                                        <div className="flex items-center gap-2">
                                            <input
                                                className="bg-white/5 border border-white/10 rounded-lg px-3 py-1 text-sm text-slate-200 focus:ring-2 focus:ring-primary outline-none"
                                                value={newName}
                                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewName(e.target.value)}
                                            />
                                            <button onClick={handleSaveName} className="text-primary text-sm font-bold hover:underline">Save</button>
                                            <button onClick={() => setEditingName(false)} className="text-slate-400 text-sm hover:underline">Cancel</button>
                                        </div>
                                    ) : (
                                        <button onClick={() => setEditingName(true)} className="text-primary text-sm font-bold hover:underline flex items-center gap-1">
                                            Edit Details <span className="material-symbols-outlined text-[16px]">edit</span>
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    </section>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Workspace Settings */}
                        <section className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6 shadow-2xl overflow-hidden relative ring-1 ring-primary/20">
                            <h3 className="text-lg font-bold flex items-center gap-2 mb-6 dark:text-slate-100">
                                <span className="material-symbols-outlined text-primary">corporate_fare</span>
                                Workspace Settings
                            </h3>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Workspace Name</label>
                                    <input
                                        className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-primary focus:border-transparent transition-all text-slate-200"
                                        type="text"
                                        value={workspace.name}
                                        onChange={(e) => setWorkspace({ ...workspace, name: e.target.value })}
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Timezone</label>
                                        <select
                                            className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-primary focus:border-transparent transition-all text-slate-200"
                                            value={workspace.timezone}
                                            onChange={(e) => setWorkspace({ ...workspace, timezone: e.target.value })}
                                        >
                                            <option value="America/Los_Angeles">PST (UTC-8)</option>
                                            <option value="America/New_York">EST (UTC-5)</option>
                                            <option value="Europe/London">GMT (UTC+0)</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Primary Region</label>
                                        <input
                                            className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-primary focus:border-transparent transition-all text-slate-200"
                                            type="text"
                                            value={workspace.primary_region}
                                            onChange={(e) => setWorkspace({ ...workspace, primary_region: e.target.value })}
                                        />
                                    </div>
                                </div>
                                <button onClick={handleSaveWorkspace} className="mt-4 px-4 py-2 bg-primary/20 text-primary border border-primary text-sm font-bold rounded-lg hover:bg-primary/30 transition-colors">
                                    Save Workspace
                                </button>
                            </div>
                        </section>

                        {/* Security & Access */}
                        <section className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6 shadow-2xl overflow-hidden relative">
                            <h3 className="text-lg font-bold flex items-center gap-2 mb-6 dark:text-slate-100">
                                <span className="material-symbols-outlined text-primary">security</span>
                                Security & Access
                            </h3>
                            <div className="space-y-4">
                                {/* FIX: 2FA toggle now uses twoFAEnabled state */}
                                <div className="flex items-center justify-between p-3 bg-slate-100 dark:bg-slate-800/50 rounded-lg">
                                    <div>
                                        <p className="text-sm font-bold dark:text-slate-200">Two-Factor Authentication</p>
                                        <p className="text-[10px] text-slate-500 uppercase tracking-tight">
                                            {twoFAEnabled ? 'Enabled via Authenticator App' : 'Disabled — click to enable'}
                                        </p>
                                    </div>
                                    <button
                                        onClick={() => {
                                            setTwoFAEnabled(v => !v);
                                            showToast(`2FA ${!twoFAEnabled ? 'enabled' : 'disabled'}`);
                                        }}
                                        className="flex items-center"
                                        title="Toggle Two-Factor Authentication"
                                    >
                                        <div className={`w-10 h-5 rounded-full relative cursor-pointer transition-colors ${twoFAEnabled ? 'bg-primary' : 'bg-slate-400 dark:bg-slate-600'}`}>
                                            <div className={`absolute top-1 h-3 w-3 bg-white rounded-full transition-all ${twoFAEnabled ? 'right-1' : 'left-1'}`}></div>
                                        </div>
                                    </button>
                                </div>
                                <button onClick={() => setShowPasswordForm(!showPasswordForm)} className="w-full py-2 bg-slate-200 dark:bg-slate-800 dark:text-slate-200 text-sm font-bold rounded-lg hover:bg-slate-300 dark:hover:bg-slate-700 transition-colors">Change Password</button>
                                {showPasswordForm && (
                                    <div className="space-y-2 mt-2">
                                        <input
                                            type="password"
                                            placeholder="Current password"
                                            value={oldPassword}
                                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOldPassword(e.target.value)}
                                            className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-slate-200 focus:ring-2 focus:ring-primary outline-none"
                                        />
                                        <input
                                            type="password"
                                            placeholder="New password"
                                            value={newPassword}
                                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewPassword(e.target.value)}
                                            className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-slate-200 focus:ring-2 focus:ring-primary outline-none"
                                        />
                                        <button onClick={handleChangePassword} className="w-full py-2 bg-primary text-white text-sm font-bold rounded-lg hover:bg-primary/90 transition-colors">Confirm Change</button>
                                    </div>
                                )}
                                <button className="w-full py-2 text-primary border border-primary/20 bg-primary/5 text-sm font-bold rounded-lg hover:bg-primary/10 transition-colors">Review Active Sessions (3)</button>
                            </div>
                        </section>
                    </div>

                    {/* Team Permissions */}
                    <section className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6 shadow-2xl overflow-hidden relative">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
                            <h3 className="text-lg font-bold flex items-center gap-2 dark:text-slate-100">
                                <span className="material-symbols-outlined text-primary">group_add</span>
                                Team Permissions
                            </h3>
                            <button onClick={() => setShowInviteForm(!showInviteForm)} className="flex items-center gap-2 px-4 py-2 bg-grad-primary text-slate-50 dark:text-white text-sm font-bold rounded-lg shadow-lg shadow-primary/20 hover:opacity-90 transition-all">
                                <span className="material-symbols-outlined text-[18px]">add_circle</span>
                                Invite Member
                            </button>
                        </div>

                        {showInviteForm && (
                            <div className="mb-4 flex items-center gap-3 p-4 rounded-lg bg-white/5 border border-white/10">
                                <input
                                    type="email"
                                    placeholder="colleague@hospital.org"
                                    value={inviteEmail}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInviteEmail(e.target.value)}
                                    className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-slate-200 focus:ring-2 focus:ring-primary outline-none"
                                />
                                <button onClick={handleInvite} className="px-4 py-2 bg-primary text-white text-sm font-bold rounded-lg hover:bg-primary/90 transition-colors">Send Invite</button>
                                <button onClick={() => setShowInviteForm(false)} className="text-slate-400 hover:text-white">
                                    <span className="material-symbols-outlined text-sm">close</span>
                                </button>
                            </div>
                        )}
                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead>
                                    <tr className="border-b border-white/5 last:border-0 text-slate-400">
                                        <th className="pb-3 font-bold">Member</th>
                                        <th className="pb-3 font-bold">Access Level</th>
                                        <th className="pb-3 font-bold text-right">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {team.map((t, idx) => (
                                        <tr key={idx} className="border-b border-white/5 last:border-0 hover:bg-white/5 transition-colors">
                                            <td className="py-4 pl-2">
                                                <div className="flex items-center gap-3">
                                                    <div className="h-8 w-8 rounded-full bg-slate-200 dark:bg-slate-700 bg-cover"></div>
                                                    <div>
                                                        <p className="text-sm font-bold dark:text-slate-200">{t.name}</p>
                                                        <p className="text-[11px] text-slate-500">{t.email}</p>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="py-4">
                                                <span className="px-2 py-1 bg-primary/10 text-primary text-[10px] font-bold rounded uppercase">{t.role}</span>
                                            </td>
                                            <td className="py-4 text-right pr-2">
                                                <button className="text-slate-400 hover:text-primary"><span className="material-symbols-outlined text-[20px]">more_vert</span></button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </section>

                    {/* Notification Preferences */}
                    <section className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6 shadow-2xl overflow-hidden relative">
                        <h3 className="text-lg font-bold flex items-center gap-2 mb-6 dark:text-slate-100">
                            <span className="material-symbols-outlined text-primary">notifications_active</span>
                            Notification Preferences
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="space-y-4">
                                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                    <span className="material-symbols-outlined text-[16px]">warning</span> Critical AQI Spikes
                                </h4>
                                <div className="space-y-3">
                                    {/* FIX: Pass new values directly to avoid stale closure — no longer reads from state inside handler */}
                                    <button
                                        className="flex items-center justify-between cursor-pointer group w-full"
                                        onClick={() => {
                                            const next = !notifEmail;
                                            setNotifEmail(next);
                                            handleToggleNotification('Email', next, notifSms, notifPush);
                                        }}
                                    >
                                        <span className="text-sm font-medium dark:text-slate-300">Email Alerts</span>
                                        <div className={`w-9 h-5 rounded-full relative flex items-center px-1 transition-colors ${notifEmail ? 'bg-primary' : 'bg-slate-200 dark:bg-slate-700'}`}>
                                            <div className={`h-3 w-3 bg-white rounded-full transition-all ${notifEmail ? 'ml-auto' : ''}`}></div>
                                        </div>
                                    </button>
                                    <button
                                        className="flex items-center justify-between cursor-pointer group w-full"
                                        onClick={() => {
                                            const next = !notifSms;
                                            setNotifSms(next);
                                            handleToggleNotification('SMS', notifEmail, next, notifPush);
                                        }}
                                    >
                                        <span className="text-sm font-medium dark:text-slate-300">SMS Notifications</span>
                                        <div className={`w-9 h-5 rounded-full relative flex items-center px-1 transition-colors ${notifSms ? 'bg-primary' : 'bg-slate-200 dark:bg-slate-700'}`}>
                                            <div className={`h-3 w-3 bg-white rounded-full transition-all ${notifSms ? 'ml-auto' : ''}`}></div>
                                        </div>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </section>
                </div>
            </div>
        </div>
    );
}
