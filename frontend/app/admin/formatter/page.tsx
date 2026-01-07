"use client";

import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { ArrowRight, Save, Wand2 } from 'lucide-react';

interface Template {
    id: string;
    name: string;
}

export default function FormatterPage() {
    const [templates, setTemplates] = useState<Template[]>([]);
    const [selectedTemplate, setSelectedTemplate] = useState<string>('');
    const [rawText, setRawText] = useState('');
    const [formattedText, setFormattedText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [publishStatus, setPublishStatus] = useState<'idle' | 'success' | 'error'>('idle');

    useEffect(() => {
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/admin/templates`)
            .then(res => res.json())
            .then(data => {
                setTemplates(data);
                if (data.length > 0) setSelectedTemplate(data[0].id);
            })
            .catch(console.error);
    }, []);

    const handleFormat = async () => {
        if (!rawText || !selectedTemplate) return;

        setIsLoading(true);
        setPublishStatus('idle');

        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/admin/kb/format`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ raw_text: rawText, template_id: selectedTemplate })
            });
            const data = await res.json();
            setFormattedText(data.formatted_text);
        } catch (error) {
            console.error("Format error:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handlePublish = async () => {
        if (!formattedText) return;

        try {
            // Mock title extraction (first line)
            const title = formattedText.split('\n')[0].replace('#', '').trim() || "Untitled KB";

            await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/admin/kb/publish`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, content: formattedText, destination: "sharepoint" })
            });
            setPublishStatus('success');
            setTimeout(() => setPublishStatus('idle'), 3000);
        } catch (error) {
            console.error("Publish error:", error);
            setPublishStatus('error');
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-100px)]">
            <h1 className="text-2xl font-bold mb-4 flex items-center gap-2">
                <Wand2 className="text-primary" /> KB Article Formatter
            </h1>

            <div className="flex gap-4 mb-4">
                <select
                    className="border rounded p-2 min-w-[200px]"
                    value={selectedTemplate}
                    onChange={e => setSelectedTemplate(e.target.value)}
                >
                    <option value="" disabled>Select Template...</option>
                    {templates.map(t => (
                        <option key={t.id} value={t.id}>{t.name}</option>
                    ))}
                </select>

                <button
                    onClick={handleFormat}
                    disabled={isLoading || !rawText}
                    className="bg-primary text-white px-6 py-2 rounded flex items-center gap-2 font-bold hover:brightness-110 disabled:grayscale transition"
                >
                    {isLoading ? <span className="animate-spin">⌛</span> : <Wand2 size={18} />}
                    {isLoading ? 'Formatting...' : 'Magic Format'}
                </button>
            </div>

            <div className="flex-1 flex gap-6 overflow-hidden">
                {/* Input Column */}
                <div className="flex-1 flex flex-col">
                    <label className="text-sm font-bold text-gray-500 mb-2 uppercase">Raw Text Input</label>
                    <textarea
                        className="flex-1 border rounded-lg p-4 font-mono text-sm resize-none focus:ring-2 focus:ring-primary/20"
                        placeholder="Paste unformatted notes, emails, or scratchpad text here..."
                        value={rawText}
                        onChange={e => setRawText(e.target.value)}
                    />
                </div>

                {/* Arrow Divider */}
                <div className="flex items-center justify-center text-gray-300">
                    <ArrowRight size={32} />
                </div>

                {/* Preview Column */}
                <div className="flex-1 flex flex-col bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden relative">
                    <div className="p-3 border-b bg-gray-50 flex justify-between items-center">
                        <label className="text-sm font-bold text-gray-500 uppercase">Live Preview</label>
                        {formattedText && (
                            <button
                                onClick={handlePublish}
                                className={`px-4 py-1.5 rounded text-sm font-bold flex items-center gap-2 transition ${publishStatus === 'success' ? 'bg-green-500 text-white' : 'bg-gray-800 text-white hover:bg-black'}`}
                            >
                                <Save size={14} />
                                {publishStatus === 'success' ? 'Published!' : 'Publish'}
                            </button>
                        )}
                    </div>
                    <div className="flex-1 overflow-y-auto p-6 prose prose-sm max-w-none">
                        {formattedText ? (
                            <ReactMarkdown>{formattedText}</ReactMarkdown>
                        ) : (
                            <div className="h-full flex items-center justify-center text-gray-400 italic">
                                Formatted content will appear here...
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
