"use client";

import { useEffect, useState } from 'react';

interface Stats {
    total_queries: number;
    total_documents: number;
    pending_feedback: number;
    total_users: number;
}

export default function AdminDashboard() {
    const [stats, setStats] = useState<Stats | null>(null);

    useEffect(() => {
        const fetchStats = () => {
            fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/admin/stats`)
                .then(res => res.json())
                .then(data => setStats(data))
                .catch(err => console.error(err));
        };

        fetchStats();
        const interval = setInterval(fetchStats, 3000); // Poll every 3 seconds

        return () => clearInterval(interval);
    }, []);

    if (!stats) return <div>Loading statistics...</div>;

    return (
        <div>
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-800 dark:text-white">System Overview</h1>
                    <p className="text-gray-500 mt-1">Real-time metrics and system health.</p>
                </div>
                <div className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold uppercase tracking-wide">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    System Online
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <StatsCard
                    title="Total Queries"
                    value={stats.total_queries}
                    icon={<svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>}
                />
                <StatsCard
                    title="Documents Indexed"
                    value={stats.total_documents}
                    icon={<svg className="w-6 h-6 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
                />
                <StatsCard
                    title="Pending Feedback"
                    value={stats.pending_feedback}
                    icon={<svg className="w-6 h-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>}
                />
                <StatsCard
                    title="Users Active"
                    value={stats.total_users}
                    icon={<svg className="w-6 h-6 text-pink-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>}
                />
            </div>

            <div className="bg-white dark:bg-zinc-900 p-8 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-800">
                <div className="flex items-center gap-4 mb-6">
                    <div className="p-3 bg-primary/10 rounded-xl text-primary">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Data Synchronization</h2>
                        <p className="text-sm text-gray-500">Trigger manual updates from connected sources.</p>
                    </div>
                </div>

                <div className="flex flex-wrap gap-4">
                    <ActionBtn label="Sync SharePoint" connector="sharepoint" />
                    <ActionBtn label="Sync Google Drive" connector="google" />
                    <div className="w-px bg-gray-200 mx-2 h-10 self-center hidden sm:block"></div>
                    <a href="/admin/documents" className="px-5 py-2.5 rounded-xl border border-gray-200 hover:bg-gray-50 dark:border-zinc-700 dark:hover:bg-zinc-800 text-gray-600 dark:text-gray-300 font-medium transition-all flex items-center gap-2">
                        View Document Index &rarr;
                    </a>
                </div>
            </div>
        </div>
    );
}

function ActionBtn({ label, connector }: { label: string, connector: string }) {
    const [loading, setLoading] = useState(false);

    const trigger = async () => {
        setLoading(true);
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
            await fetch(`${apiUrl}/sync/trigger?connector=${connector}`, { method: 'POST' });
            alert(`Sync triggered for ${connector}`);
        } catch (e) {
            alert('Failed to trigger sync');
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <button
            onClick={trigger}
            disabled={loading}
            className="bg-primary hover:bg-primary/90 disabled:opacity-50 text-white px-5 py-2.5 rounded-xl transition-all shadow-sm hover:shadow hover:-translate-y-0.5 flex items-center gap-2 font-medium"
        >
            {loading ? (
                <>
                    <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    <span>Syncing...</span>
                </>
            ) : (
                label
            )}
        </button>
    );
}

function StatsCard({ title, value, icon }: { title: string, value: number, icon: React.ReactNode }) {
    return (
        <div className="glass-card p-6 flex items-start justify-between group hover:border-primary/20 transition-all duration-300">
            <div>
                <p className="text-gray-500 dark:text-gray-400 text-xs font-bold uppercase tracking-wider mb-1">{title}</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1 group-hover:scale-105 transition-transform origin-left">{value}</p>
            </div>
            <div className="p-3 bg-gray-50 dark:bg-zinc-800 rounded-xl group-hover:bg-primary/10 transition-colors">
                {icon}
            </div>
        </div>
    );
}
