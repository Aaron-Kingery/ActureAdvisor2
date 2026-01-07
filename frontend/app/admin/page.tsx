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
            <h1 className="text-3xl font-bold text-gray-800 mb-8">System Overview</h1>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <StatsCard title="Total Queries" value={stats.total_queries} color="bg-blue-500" />
                <StatsCard title="Documents Indexed" value={stats.total_documents} color="bg-green-500" />
                <StatsCard title="Pending Feedback" value={stats.pending_feedback} color="bg-yellow-500" />
                <StatsCard title="Total Users" value={stats.total_users} color="bg-purple-500" />
            </div>

            <div className="mt-8 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <h2 className="text-xl font-semibold mb-4">Data Sync Actions</h2>
                <div className="flex gap-4">
                    <ActionBtn label="Sync SharePoint" connector="sharepoint" />
                    <ActionBtn label="Sync Google Drive" connector="google" />
                    <div className="border-l border-gray-200 mx-2"></div>
                    <a href="/admin/documents" className="border border-primary text-primary px-4 py-2 rounded hover:bg-gray-50 flex items-center gap-2">
                        View Documents
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
            className="bg-primary text-white px-4 py-2 rounded hover:opacity-90 disabled:opacity-50 flex items-center gap-2"
        >
            {loading ? 'Syncing...' : label}
        </button>
    );
}


function StatsCard({ title, value, color }: { title: string, value: number, color: string }) {
    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center justify-between">
            <div>
                <p className="text-gray-500 text-sm font-medium uppercase">{title}</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
            </div>
            <div className={`w-3 h-3 rounded-full ${color}`}></div>
        </div>
    );
}
