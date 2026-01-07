"use client";

import { useEffect, useState } from 'react';

interface Stats {
    total_queries: int;
    total_documents: int;
    pending_feedback: int;
    total_users: int;
}

export default function AdminDashboard() {
    const [stats, setStats] = useState<Stats | null>(null);

    useEffect(() => {
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/admin/stats`)
            .then(res => res.json())
            .then(data => setStats(data))
            .catch(err => console.error(err));
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
                <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
                <div className="flex gap-4">
                    <button className="bg-acture-primary text-white px-4 py-2 rounded hover:opacity-90">
                        Upload New Document
                    </button>
                    <button className="border border-acture-primary text-acture-primary px-4 py-2 rounded hover:bg-gray-50">
                        View Recent Logs
                    </button>
                </div>
            </div>
        </div>
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
