import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, ExternalLink } from 'lucide-react'
import { api, type Stats } from '../api/client'

interface Doc {
  id: string
  title: string
  file_type: string
  source_url: string
  last_synced: string
}

export default function Documents() {
  const [docs, setDocs] = useState<Doc[]>([])
  const [stats, setStats] = useState<Stats | null>(null)

  useEffect(() => {
    api.stats().then(setStats).catch(() => {})
    // Fetch documents from admin endpoint
    fetch('/api/admin/documents', { credentials: 'include' })
      .then((r) => r.json())
      .then(setDocs)
      .catch(() => {})
  }, [])

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Link to="/admin" className="text-gray-400 hover:text-gray-600">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-2xl font-bold text-gray-800">Document Index</h1>
        {stats && (
          <span className="text-sm text-gray-400 ml-auto">{stats.total_documents} documents</span>
        )}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wide">
              <th className="px-4 py-3">Title</th>
              <th className="px-4 py-3 w-20">Type</th>
              <th className="px-4 py-3 w-40">Last Synced</th>
              <th className="px-4 py-3 w-16"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {docs.map((doc) => (
              <tr key={doc.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-gray-700 truncate max-w-xs">{doc.title}</td>
                <td className="px-4 py-3">
                  <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded">
                    {doc.file_type}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">
                  {new Date(doc.last_synced).toLocaleString()}
                </td>
                <td className="px-4 py-3">
                  <a
                    href={doc.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-acture-accent hover:text-acture-primary"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {docs.length === 0 && (
          <div className="text-center py-8 text-gray-400 text-sm">No documents found.</div>
        )}
      </div>
    </div>
  )
}
