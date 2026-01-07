"use client";

import { useSession, signIn, signOut } from "next-auth/react";
import ChatInterface from "@/components/ChatInterface";
import { LogOut } from "lucide-react";

export default function Home() {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-secondary/10">
        <div className="p-8 bg-white dark:bg-zinc-900 rounded-lg shadow-lg max-w-md w-full text-center border border-gray-200 dark:border-gray-800">
          <h1 className="text-3xl font-bold text-primary mb-2">Acture Advisor</h1>
          <p className="text-gray-600 mb-8">Internal Knowledge Assistant</p>

          <button
            onClick={() => signIn()}
            className="w-full bg-primary hover:bg-primary/90 text-white font-medium py-3 px-4 rounded transition-colors"
          >
            Sign In with SSO
          </button>
        </div>
      </div>
    );
  }

  return (
    <main className="flex flex-col h-screen overflow-hidden">
      {/* Header */}
      {/* Header */}
      <header className="flex-none glass border-b border-white/20 z-10 py-3 px-6 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="relative w-8 h-8 bg-white rounded-lg overflow-hidden shadow-sm flex items-center justify-center">
            {/* Using the logo image */}
            <img src="/logo-acture.svg" alt="Acture" className="object-contain w-full h-full" />
          </div>
          <div>
            <h1 className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-[#9D4EDD] tracking-tight">
              Acture Advisor 2.0
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex flex-col items-end">
            <span className="text-sm font-semibold text-gray-700 dark:text-gray-200">
              {session.user?.name}
            </span>
            <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">
              {session.user?.email}
            </span>
          </div>
          <button
            onClick={() => signOut()}
            className="p-2 text-gray-500 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-full transition-all duration-300"
            title="Sign Out"
          >
            <LogOut size={18} />
          </button>
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-hidden relative">
        <ChatInterface />
      </div>
    </main>
  );
}
