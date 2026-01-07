"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Send, ThumbsUp, ThumbsDown, Bot, User, FileText, AlertCircle } from "lucide-react";
import clsx from "clsx";

interface Source {
    title: string;
    url: string;
}

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    sources?: Source[];
    feedback?: "positive" | "negative";
}

export default function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    const [docCount, setDocCount] = useState<number | null>(null);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
                const res = await fetch(`${apiUrl}/admin/stats`);
                if (res.ok) {
                    const data = await res.json();
                    setDocCount(data.total_documents);
                }
            } catch (error) {
                console.error("Failed to fetch doc stats:", error);
            }
        };
        fetchStats();
    }, []);

    const handleFeedback = async (messageId: string, type: "positive" | "negative") => {
        // Optimistic UI update
        setMessages((prev) =>
            prev.map((msg) =>
                msg.id === messageId ? { ...msg, feedback: type } : msg
            )
        );

        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
            await fetch(`${apiUrl}/chat/${messageId}/feedback`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ feedback_type: type }),
            });
        } catch (error) {
            console.error("Failed to submit feedback:", error);
            // Revert on error? For now, just log.
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: "user",
            content: input,
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setIsLoading(true);

        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
            const res = await fetch(`${apiUrl}/chat/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message: userMessage.content }),
            });

            if (!res.ok) {
                throw new Error("Failed to fetch response");
            }

            const data = await res.json();

            const botMessage: Message = {
                id: data.query_id || Date.now().toString(),
                role: "assistant",
                content: data.response,
                sources: data.sources,
            };

            setMessages((prev) => [...prev, botMessage]);
        } catch (error) {
            console.error("Chat error:", error);
            const errorMessage: Message = {
                id: Date.now().toString(),
                role: "assistant",
                content: "Sorry, I encountered an error regarding your request. Please try again.",
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
            // Focus input after response (optional, good for desktop)
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    };

    return (
        <div className="flex flex-col h-full w-full bg-secondary/5 relative">
            {/* Background Decor */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden">
                <div className="absolute top-[20%] left-[10%] w-96 h-96 bg-primary/5 rounded-full blur-3xl opacity-50" />
                <div className="absolute bottom-[20%] right-[10%] w-96 h-96 bg-accent/20 rounded-full blur-3xl opacity-50" />
            </div>

            {/* Messages List - Scrollbar at viewport edge */}
            <div className="flex-1 overflow-y-auto z-0">
                <div className="max-w-4xl mx-auto p-4 space-y-8 py-8">
                    {messages.length === 0 && (
                        <div className="h-full flex flex-col items-center justify-center text-gray-400 opacity-60 min-h-[50vh]">
                            <div className="w-20 h-20 bg-white dark:bg-zinc-800 rounded-2xl flex items-center justify-center shadow-lg mb-6 border border-gray-100 dark:border-zinc-700">
                                <Bot size={40} className="text-primary" />
                            </div>
                            <p className="text-xl font-medium text-gray-500">How can I help you today?</p>
                        </div>
                    )}

                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={clsx(
                                "flex w-full animate-fade-in-up",
                                msg.role === "user" ? "justify-end" : "justify-start"
                            )}
                        >
                            <div
                                className={clsx(
                                    "flex max-w-[85%] sm:max-w-[75%] rounded-3xl p-5 shadow-sm transition-all hover:shadow-md",
                                    msg.role === "user"
                                        ? "bg-gradient-to-r from-primary to-[#8B4DA3] text-white rounded-br-none"
                                        : "bg-white dark:bg-zinc-800 border border-gray-100 dark:border-zinc-700 rounded-bl-none"
                                )}
                            >
                                <div className="mr-4 mt-1 flex-shrink-0">
                                    {msg.role === "user" ? (
                                        <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-white">
                                            <User size={16} />
                                        </div>
                                    ) : (
                                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                                            <Bot size={18} />
                                        </div>
                                    )}
                                </div>

                                <div className="flex-1 min-w-0">
                                    <div className={clsx(
                                        "prose prose-sm max-w-none break-words leading-relaxed",
                                        msg.role === "user" ? "prose-invert text-white/95" : "dark:prose-invert text-gray-700 dark:text-gray-200"
                                    )}>
                                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                                    </div>

                                    {/* Sources */}
                                    {msg.sources && msg.sources.length > 0 && (
                                        <div className="mt-5 pt-3 border-t border-gray-100/50 dark:border-zinc-700/50">
                                            <p className="text-[10px] font-bold text-gray-400 mb-2 uppercase tracking-widest flex items-center gap-1">
                                                <FileText size={10} /> Sources
                                            </p>
                                            <div className="flex flex-wrap gap-2">
                                                {msg.sources.map((source, idx) => (
                                                    <a
                                                        key={idx}
                                                        href={source.url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 hover:bg-gray-100 dark:bg-zinc-700/50 dark:hover:bg-zinc-700 text-gray-600 dark:text-gray-300 rounded-lg text-xs font-medium transition-colors border border-gray-100 dark:border-zinc-600"
                                                    >
                                                        <span className="truncate max-w-[150px]">{source.title}</span>
                                                    </a>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Feedback Actions */}
                                    {msg.role === "assistant" && (
                                        <div className="mt-3 flex items-center justify-end gap-3 text-gray-400/80">
                                            <button
                                                onClick={() => handleFeedback(msg.id, "positive")}
                                                className={clsx(
                                                    "p-1.5 rounded-full hover:bg-green-50 dark:hover:bg-green-900/20 transition-all",
                                                    msg.feedback === "positive" ? "text-green-500 bg-green-50" : "hover:text-green-500"
                                                )}
                                            >
                                                <ThumbsUp size={14} className={clsx(msg.feedback === "positive" && "fill-current")} />
                                            </button>
                                            <button
                                                onClick={() => handleFeedback(msg.id, "negative")}
                                                className={clsx(
                                                    "p-1.5 rounded-full hover:bg-red-50 dark:hover:bg-red-900/20 transition-all",
                                                    msg.feedback === "negative" ? "text-red-500 bg-red-50" : "hover:text-red-500"
                                                )}
                                            >
                                                <ThumbsDown size={14} className={clsx(msg.feedback === "negative" && "fill-current")} />
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex justify-start w-full animate-pulse">
                            <div className="bg-white dark:bg-zinc-800 border border-gray-100 dark:border-zinc-700 rounded-3xl rounded-bl-none p-5 shadow-sm flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                                    <Bot size={18} />
                                </div>
                                <div className="flex gap-1.5">
                                    <div className="w-2 h-2 bg-primary/40 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                    <div className="w-2 h-2 bg-primary/40 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                    <div className="w-2 h-2 bg-primary/40 rounded-full animate-bounce"></div>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Area (Glassmorphic Floating Pill) */}
            <div className="p-6 bg-gradient-to-t from-white via-white/80 to-transparent dark:from-black dark:via-black/80 z-10 w-full">
                <div className="max-w-3xl mx-auto">
                    <form onSubmit={handleSubmit} className="relative group">
                        <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full opacity-0 group-hover:opacity-20 transition-opacity duration-500" />
                        <div className="relative flex items-center bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 shadow-2xl shadow-primary/5 rounded-full p-2 pl-6 transition-all focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary/50">
                            <input
                                ref={inputRef}
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Ask about internal documents..."
                                className="flex-1 bg-transparent border-none text-foreground focus:ring-0 placeholder:text-gray-400 py-2.5"
                                disabled={isLoading}
                            />
                            <button
                                type="submit"
                                disabled={!input.trim() || isLoading}
                                className="ml-2 w-10 h-10 bg-primary hover:bg-primary/90 disabled:bg-gray-200 disabled:cursor-not-allowed text-white rounded-full flex items-center justify-center transition-all transform hover:scale-105 active:scale-95 shadow-md"
                            >
                                <Send size={18} className={isLoading ? "animate-pulse" : ""} />
                            </button>
                        </div>
                    </form>
                    <div className="text-center mt-3 flex justify-center items-center gap-3 opacity-60 hover:opacity-100 transition-opacity">
                        <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wider">Acture Advisor AI</p>
                        {docCount !== null && (
                            <span className="flex items-center gap-1.5 text-[10px] px-2 py-0.5 bg-gray-100 dark:bg-zinc-800 text-gray-500 rounded-full">
                                <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                                {docCount} Docs
                            </span>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
