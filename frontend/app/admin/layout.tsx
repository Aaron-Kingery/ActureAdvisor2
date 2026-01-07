"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import Link from 'next/link';

export default function AdminLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { data: session, status } = useSession();
    const router = useRouter();

    useEffect(() => {
        // In real app, check specifically for ADMIN role
        // For now, simple auth check + maybe email check if needed
        if (status === "unauthenticated") {
            router.push("/");
        }
    }, [status, router]);

    if (status === "loading") {
        return <div className="min-h-screen bg-gray-50 flex items-center justify-center">Loading...</div>;
    }

    return (
        <div className="min-h-screen bg-gray-50 flex">
            {/* Sidebar */}
            <aside className="w-64 bg-primary text-white p-6 shadow-xl">
                <div className="text-2xl font-bold mb-8 text-accent">Admin Console</div>
                <nav className="space-y-4">
                    <Link href="/admin" className="block p-3 rounded hover:bg-white/10 transition">
                        Dashboard
                    </Link>
                    <Link href="/admin/feedback" className="block p-3 rounded hover:bg-white/10 transition">
                        Feedback Review
                    </Link>
                    <Link href="/admin/templates" className="block p-3 rounded hover:bg-white/10 transition">
                        KB Templates
                    </Link>
                    <div className="h-px bg-white/20 my-4"></div>
                    <Link href="/" className="block p-3 rounded hover:bg-white/10 transition text-sm opacity-80">
                        &larr; Back to Chat
                    </Link>
                </nav>
            </aside>

            {/* Main Content */}
            <main className="flex-1 p-8 overflow-y-auto">
                {children}
            </main>
        </div>
    );
}
