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
      <header className="flex-none bg-primary text-white p-4 shadow-md flex justify-between items-center z-10">
        <div className="flex items-center space-x-2">
          {/* Placeholder Logo */}
          <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center font-bold">
            A
          </div>
          <h1 className="text-xl font-bold">Acture Advisor 2.0</h1>
        </div>
        <div className="flex items-center space-x-4">
          <span className="text-sm opacity-90 hidden sm:inline">
            {session.user?.name}
          </span>
          <button
            onClick={() => signOut()}
            className="p-2 hover:bg-white/10 rounded-full transition-colors"
            title="Sign Out"
          >
            <LogOut size={20} />
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
