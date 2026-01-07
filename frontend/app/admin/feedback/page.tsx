"use client";

import { useEffect, useState } from 'react';

interface FeedbackItem {
    id: string;
    feedback_type: string; // 'up' or 'down'
    status: 'new' | 'reviewed' | 'resolved';
    query_text: string;
    response_text: string;
    admin_notes: string | null;
    created_at: string;
    user_email: string | null;
}

export default function FeedbackPage() {
    const [feedback, setFeedback] = useState<FeedbackItem[]>([]);
    const [selectedItem, setSelectedItem] = useState<FeedbackItem | null>(null);

    const fetchFeedback = () => {
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/admin/feedback`)
            .then(res => res.json())
            .then(data => setFeedback(data))
            .catch(console.error);
    };

    useEffect(() => {
        fetchFeedback();
    }, []);

    const updateStatus = async (id: string, status: string, notes: string | null) => {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/admin/feedback/${id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status, admin_notes: notes })
        });
        fetchFeedback();
        setSelectedItem(null);
    };

    return (
        <div className="flex h-[calc(100vh-100px)] gap-6">
            <div className="w-1/2 overflow-y-auto">
                <h1 className="text-2xl font-bold mb-6">Feedback Queue</h1>
                <div className="space-y-4">
                    {feedback.map(item => (
                        <div
                            key={item.id}
                            onClick={() => setSelectedItem(item)}
                            className={`p-4 bg-white rounded-lg shadow-sm cursor-pointer border hover:border-primary transition ${selectedItem?.id === item.id ? 'border-primary ring-1 ring-primary' : 'border-gray-200'}`}
                        >
                            <div className="flex justify-between items-start mb-2">
                                <span className={`px-2 py-1 rounded text-xs font-bold ${item.feedback_type === 'up' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                    {item.feedback_type === 'up' ? 'THUMBS UP' : 'THUMBS DOWN'}
                                </span>
                                <span className={`text-xs uppercase ${item.status === 'new' ? 'text-blue-600 font-bold' : 'text-gray-500'}`}>
                                    {item.status}
                                </span>
                            </div>
                            <div className="mb-2">
                                <p className="text-xs font-semibold text-gray-500 mb-1">{item.user_email || 'Unknown User'}</p>
                                <p className="text-sm text-gray-800 line-clamp-2">{item.query_text}</p>
                            </div>
                            <p className="text-xs text-gray-400 mt-2">{new Date(item.created_at).toLocaleString()}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* Detail View */}
            <div className="w-1/2 bg-white rounded-xl shadow p-6 overflow-y-auto">
                {selectedItem ? (
                    <div>
                        <h2 className="text-xl font-bold mb-4">Review Feedback</h2>

                        <div className="mb-6">
                            <label className="text-xs font-bold text-gray-400 uppercase">User</label>
                            <div className="bg-gray-50 p-3 rounded mt-1 text-sm font-semibold">{selectedItem.user_email || 'Unknown User'}</div>
                        </div>

                        <div className="mb-6">
                            <label className="text-xs font-bold text-gray-400 uppercase">User Query</label>
                            <div className="bg-gray-50 p-3 rounded mt-1 text-sm">{selectedItem.query_text}</div>
                        </div>

                        <div className="mb-6">
                            <label className="text-xs font-bold text-gray-400 uppercase">AI Response</label>
                            <div className="bg-gray-50 p-3 rounded mt-1 text-sm whitespace-pre-wrap">{selectedItem.response_text}</div>
                        </div>

                        <div className="mb-6">
                            <label className="text-xs font-bold text-gray-400 uppercase">Admin Notes</label>
                            <textarea
                                className="w-full border rounded p-2 mt-1 text-sm h-24"
                                defaultValue={selectedItem.admin_notes || ''}
                                id="notesInput"
                            />
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={() => updateStatus(selectedItem.id, 'resolved', (document.getElementById('notesInput') as HTMLTextAreaElement).value)}
                                className="bg-primary text-white px-4 py-2 rounded hover:opacity-90"
                            >
                                Mark Resolved
                            </button>
                            <button
                                onClick={() => updateStatus(selectedItem.id, 'reviewed', (document.getElementById('notesInput') as HTMLTextAreaElement).value)}
                                className="bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300"
                            >
                                Mark Reviewed
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="h-full flex items-center justify-center text-gray-400">
                        Select an item to review details.
                    </div>
                )}
            </div>
        </div>
    );
}
