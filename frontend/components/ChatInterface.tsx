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

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

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
        <div className="flex flex-col h-full max-w-4xl mx-auto">
            {/* Messages List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {messages.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400 opacity-60">
                        <Bot size={64} className="mb-4" />
                        <p className="text-lg">Ask me anything about Acture's internal documents.</p>
                    </div>
                )}

                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={clsx(
                            "flex w-full",
                            msg.role === "user" ? "justify-end" : "justify-start"
                        )}
                    >
                        <div
                            className={clsx(
                                "flex max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 shadow-sm",
                                msg.role === "user"
                                    ? "bg-primary text-white rounded-br-none"
                                    : "bg-white dark:bg-zinc-800 border border-gray-100 dark:border-zinc-700 rounded-bl-none"
                            )}
                        >
                            <div className="mr-3 mt-1 flex-shrink-0">
                                {msg.role === "user" ? (
                                    <User size={20} className="opacity-80" />
                                ) : (
                                    <Bot size={20} className="text-primary dark:text-accent" />
                                )}
                            </div>

                            <div className="flex-1 min-w-0">
                                <div className="prose prose-sm dark:prose-invert max-w-none break-words">
                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                </div>

                                {/* Sources */}
                                {msg.sources && msg.sources.length > 0 && (
                                    <div className="mt-4 pt-3 border-t border-gray-100 dark:border-zinc-700">
                                        <p className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">Sources</p>
                                        <div className="flex flex-wrap gap-2">
                                            {msg.sources.map((source, idx) => (
                                                <a
                                                    key={idx}
                                                    href={source.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="flex items-center gap-1.5 px-3 py-1.5 bg-accent/20 hover:bg-accent/40 text-primary dark:text-accent rounded-full text-xs font-medium transition-colors border border-accent/20"
                                                >
                                                    <FileText size={12} />
                                                    <span className="truncate max-w-[150px]">{source.title}</span>
                                                </a>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Feedback Actions (Assistant only) */}
                                {msg.role === "assistant" && (
                                    <div className="mt-2 flex items-center justify-end gap-2 text-gray-400">
                                        <button className="p-1 hover:text-green-500 transition-colors" title="Helpful">
                                            <ThumbsUp size={14} />
                                        </button>
                                        <button className="p-1 hover:text-red-500 transition-colors" title="Not Helpful">
                                            <ThumbsDown size={14} />
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="flex justify-start w-full">
                        <div className="bg-white dark:bg-zinc-800 border border-gray-100 dark:border-zinc-700 rounded-2xl rounded-bl-none p-4 shadow-sm flex items-center gap-2">
                            <Bot size={20} className="text-primary dark:text-accent" />
                            <div className="flex gap-1">
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-white dark:bg-zinc-900 border-t border-gray-200 dark:border-zinc-800">
                <form onSubmit={handleSubmit} className="flex gap-2 max-w-4xl mx-auto relative">
                    <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask a question..."
                        className="flex-1 bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 text-foreground rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent transition-all"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || isLoading}
                        className="bg-primary hover:bg-primary/90 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-xl px-5 py-3 transition-colors flex items-center justify-center font-medium shadow-sm"
                    >
                        <Send size={20} />
                    </button>
                </form>
                <div className="text-center mt-2">
                    <p className="text-xs text-gray-400">Acture Advisor can make mistakes. Please verify important information.</p>
                </div>
            </div>
        </div>
    );
}
