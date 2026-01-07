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
        <div className="min-h-screen bg-gray-50 dark:bg-zinc-950 flex font-sans">
            {/* Sidebar */}
            <aside className="w-64 bg-[#2D2D2D] text-white flex flex-col shadow-2xl z-20">
                <div className="p-6 border-b border-white/10 flex flex-col items-start gap-4">
                    <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center overflow-hidden p-1 shadow-lg">
                        <img
                            src="/logo-acture.svg"
                            alt="Acture Logo"
                            className="w-full h-full object-contain"
                        />
                    </div>
                    <div>
                        <div className="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                            Admin Console
                        </div>
                        <p className="text-xs text-gray-400 mt-1 uppercase tracking-widest">Acture Advisor</p>
                    </div>
                </div>

                <nav className="flex-1 p-4 space-y-1">
                    <NavLink href="/admin" label="Dashboard" />
                    <NavLink href="/admin/feedback" label="Feedback Review" />
                    <NavLink href="/admin/templates" label="KB Templates" />
                    <NavLink href="/admin/formatter" label="KB Formatter" />
                </nav>

                <div className="p-4 border-t border-white/10">
                    <Link
                        href="/"
                        className="flex items-center gap-2 p-3 rounded-xl hover:bg-white/5 text-gray-400 hover:text-white transition-all group"
                    >
                        <span className="group-hover:-translate-x-1 transition-transform">&larr;</span>
                        <span className="text-sm font-medium">Back to Chat</span>
                    </Link>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 p-8 overflow-y-auto relative">
                {/* Subtle Background Decor */}
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/5 rounded-full blur-3xl pointer-events-none" />
                <div className="relative z-10 max-w-7xl mx-auto">
                    {children}
                </div>
            </main>
        </div>
    );
}

function NavLink({ href, label }: { href: string, label: string }) {
    // In a real app we'd check active path, for now simple styling
    return (
        <Link
            href={href}
            className="block px-4 py-3 rounded-xl text-gray-300 hover:bg-white/10 hover:text-white transition-all duration-200 text-sm font-medium"
        >
            {label}
        </Link>
    );
}
