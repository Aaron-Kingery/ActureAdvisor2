"use client";

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, FileText, ExternalLink } from 'lucide-react';

interface DocumentInfo {
    id: string;
    title: string;
    source_url: string;
    file_type: string;
    last_synced: string;
}

export default function DocumentsPage() {
    const [documents, setDocuments] = useState<DocumentInfo[]>([]);
    const [loading, setLoading] = useState(true);
    const [skip, setSkip] = useState(0);
    const limit = 50;

    useEffect(() => {
        const fetchDocs = async () => {
            setLoading(true);
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
                const res = await fetch(`${apiUrl}/admin/documents?skip=${skip}&limit=${limit}`);
                if (res.ok) {
                    const data = await res.json();
                    setDocuments(data);
                }
            } catch (error) {
                console.error("Failed to fetch documents:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchDocs();
    }, [skip]); // Refetch when skip changes

    const handlePrevious = () => {
        setSkip(prev => Math.max(0, prev - limit));
    };

    const handleNext = () => {
        setSkip(prev => prev + limit);
    };

    return (
        <div className="p-6">
            <div className="mb-6 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Link href="/admin" className="text-gray-500 hover:text-gray-900 transition-colors">
                        <ArrowLeft size={20} />
                    </Link>
                    <h1 className="text-2xl font-bold text-gray-800">Indexed Documents</h1>
                </div>
            </div>

            {loading ? (
                <div className="flex justify-center p-12">
                    <div className="text-gray-400">Loading documents...</div>
                </div>
            ) : documents.length === 0 && skip === 0 ? (
                <div className="text-gray-500 italic">No documents indexed yet.</div>
            ) : (
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-gray-50 text-gray-500 text-sm uppercase border-b border-gray-100">
                                    <th className="p-4 font-medium">Title</th>
                                    <th className="p-4 font-medium">Type</th>
                                    <th className="p-4 font-medium">Last Synced</th>
                                    <th className="p-4 font-medium">Source</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {documents.map((doc) => (
                                    <tr key={doc.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="p-4 text-gray-900 font-medium">
                                            <div className="flex items-center gap-2">
                                                <FileText size={16} className="text-primary opacity-60" />
                                                <div className="truncate max-w-md" title={doc.title}>
                                                    {doc.title}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="p-4 text-gray-500 text-sm uppercase">{doc.file_type}</td>
                                        <td className="p-4 text-gray-500 text-sm whitespace-nowrap">
                                            {new Date(doc.last_synced).toLocaleString()}
                                        </td>
                                        <td className="p-4">
                                            <a href={doc.source_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline flex items-center gap-1 text-sm">
                                                Open <ExternalLink size={12} />
                                            </a>
                                        </td>
                                    </tr>
                                ))}
                                {documents.length === 0 && skip > 0 && (
                                    <tr>
                                        <td colSpan={4} className="p-8 text-center text-gray-500">
                                            No more documents found.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination Controls */}
                    <div className="p-4 border-t border-gray-100 flex items-center justify-between bg-gray-50/50">
                        <button
                            onClick={handlePrevious}
                            disabled={skip === 0}
                            className="px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            Previous
                        </button>
                        <span className="text-sm text-gray-500">
                            Showing {skip + 1}-{skip + documents.length}
                        </span>
                        <button
                            onClick={handleNext}
                            disabled={documents.length < limit}
                            className="px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            Next
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
