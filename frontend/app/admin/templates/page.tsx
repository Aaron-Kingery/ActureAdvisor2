"use client";

import { useEffect, useState } from 'react';

interface Template {
    id: string;
    name: string;
    template_content: string;
}

export default function TemplatesPage() {
    const [templates, setTemplates] = useState<Template[]>([]);
    const [name, setName] = useState('');
    const [content, setContent] = useState('');

    const fetchTemplates = () => {
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/admin/templates`)
            .then(res => res.json())
            .then(setTemplates)
            .catch(console.error);
    };

    useEffect(() => {
        fetchTemplates();
    }, []);

    const createTemplate = async (e: React.FormEvent) => {
        e.preventDefault();
        await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/admin/templates`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, template_content: content })
        });
        setName('');
        setContent('');
        fetchTemplates();
    };

    return (
        <div>
            <h1 className="text-2xl font-bold mb-6">Knowledge Base Templates</h1>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* List */}
                <div className="space-y-4">
                    {templates.length === 0 && <p className="text-gray-500">No templates defined.</p>}
                    {templates.map(t => (
                        <div key={t.id} className="bg-white p-4 rounded shadow-sm border border-gray-200">
                            <h3 className="font-bold text-primary">{t.name}</h3>
                            <pre className="mt-2 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                                {t.template_content}
                            </pre>
                        </div>
                    ))}
                </div>

                {/* Create Form */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 h-fit">
                    <h2 className="text-lg font-bold mb-4">Create New Template</h2>
                    <form onSubmit={createTemplate}>
                        <div className="mb-4">
                            <label className="block text-sm font-medium mb-1">Template Name</label>
                            <input
                                type="text"
                                className="w-full border rounded p-2"
                                value={name}
                                onChange={e => setName(e.target.value)}
                                required
                            />
                        </div>
                        <div className="mb-4">
                            <label className="block text-sm font-medium mb-1">Content Format</label>
                            <textarea
                                className="w-full border rounded p-2 h-32 font-mono text-sm"
                                value={content}
                                onChange={e => setContent(e.target.value)}
                                placeholder="Use Markdown..."
                                required
                            />
                        </div>
                        <button type="submit" className="w-full bg-primary text-white py-2 rounded font-bold hover:brightness-110">
                            Save Template
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}
