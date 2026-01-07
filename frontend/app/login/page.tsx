"use client";

import { signIn } from "next-auth/react";
import Image from "next/image";
import { useState } from "react";

export default function LoginPage() {
    const [isLoading, setIsLoading] = useState(false);

    const handleLogin = async (provider: string) => {
        setIsLoading(true);
        await signIn(provider, { callbackUrl: "/" });
    };

    return (
        <main className="min-h-screen grid grid-cols-1 lg:grid-cols-2 overflow-hidden bg-background">
            {/* Left Column: Glass Login Form */}
            <div className="flex flex-col justify-center items-center p-8 lg:p-16 relative z-10">
                <div className="absolute inset-0 pointer-events-none">
                    {/* Subtle background blob for the left side */}
                    <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-primary/5 rounded-full blur-3xl opacity-50" />
                </div>

                <div className="glass-card w-full max-w-md p-8 sm:p-12 border-white/20 dark:border-white/10 relative overflow-hidden group hover:border-primary/30 transition-colors duration-500">

                    {/* Logo Section */}
                    <div className="flex flex-col items-center mb-10">
                        <div className="relative w-48 h-16 mb-6">
                            <Image
                                src="/logo-acture.svg"
                                alt="Acture Solutions"
                                fill
                                className="object-contain"
                                priority
                            />
                        </div>
                        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-[#9D4EDD] mb-2 tracking-tight">
                            Acture Advisor 2.0
                        </h1>
                        <p className="text-sm text-gray-500 font-medium tracking-wide uppercase">Internal Knowledge Base</p>
                    </div>

                    {/* Login Actions */}
                    <div className="space-y-4">
                        <button
                            onClick={() => handleLogin('google')}
                            disabled={isLoading}
                            className="w-full flex items-center justify-center gap-3 py-3.5 px-4 bg-white dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 rounded-xl hover:scale-[1.02] active:scale-[0.98] hover:shadow-lg transition-all duration-200 group/btn"
                        >
                            <img src="https://authjs.dev/img/providers/google.svg" className="w-5 h-5 group-hover/btn:rotate-12 transition-transform duration-300" alt="Google" />
                            <span className="font-semibold text-gray-700 dark:text-gray-200">Sign in with Google</span>
                        </button>

                        <button
                            onClick={() => handleLogin('azure-ad')}
                            disabled={isLoading}
                            className="w-full flex items-center justify-center gap-3 py-3.5 px-4 bg-[#2F2F2F] text-white rounded-xl hover:scale-[1.02] active:scale-[0.98] hover:shadow-lg hover:bg-black transition-all duration-200"
                        >
                            <img src="https://authjs.dev/img/providers/microsoft-entra-id.svg" className="w-5 h-5 invert" alt="Microsoft" />
                            <span className="font-semibold">Sign in with Microsoft</span>
                        </button>
                    </div>

                    <div className="mt-8 text-center">
                        <p className="text-xs text-gray-400">
                            Authorized personnel only. <br />All activity is monitored.
                        </p>
                    </div>
                </div>
            </div>

            {/* Right Column: Hero Gradient Mesh */}
            <div className="hidden lg:flex relative bg-black items-center justify-center overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-primary via-[#4a1c61] to-black opacity-90 animate-gradient" />

                {/* Animated Orbs */}
                <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-accent rounded-full blur-[128px] opacity-20 animate-pulse" />
                <div className="absolute bottom-1/4 left-1/4 w-[500px] h-[500px] bg-primary rounded-full blur-[150px] opacity-30" />

                <div className="relative z-10 p-12 text-white max-w-xl">
                    <h2 className="text-5xl font-bold mb-6 leading-tight">
                        Instant answers from <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent to-white">Internal Docs</span>.
                    </h2>
                    <p className="text-lg text-gray-300 leading-relaxed opacity-90">
                        Leverage the power of RAG AI to search across SharePoint and Drive.
                        Secure, accurate, and always compliant.
                    </p>

                    {/* Glass Stat Card Decor */}
                    <div className="mt-12 p-6 glass rounded-xl border border-white/10 max-w-xs transform rotate-3 hover:rotate-0 transition-transform duration-500">
                        <div className="flex items-center gap-4 mb-3">
                            <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center text-green-400">
                                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                            </div>
                            <div>
                                <p className="text-xs text-gray-400 uppercase font-bold">Success Rate</p>
                                <p className="text-xl font-bold text-white">99.8%</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}
