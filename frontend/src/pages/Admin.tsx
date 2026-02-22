import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { MessageSquare, FileText, AlertCircle, Users, RefreshCw } from 'lucide-react'
import { api, type Stats } from '../api/client'

export default function Admin() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [syncing, setSyncing] = useState(false)

  useEffect(() => {
    const load = () => api.stats().then(setStats).catch(() => {})
    load()
    const interval = setInterval(load, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleSync = async (connector: string) => {
    setSyncing(true)
    try {
      await api.syncTrigger(connector)
    } catch {}
    setTimeout(() => setSyncing(false), 3000)
  }

  const cards = stats
    ? [
        { label: 'Total Queries', value: stats.total_queries, icon: MessageSquare, color: 'text-acture-accent' },
        { label: 'Documents Indexed', value: stats.total_documents, icon: FileText, color: 'text-acture-success' },
        { label: 'Pending Feedback', value: stats.pending_feedback, icon: AlertCircle, color: 'text-acture-warning' },
        { label: 'Active Users', value: stats.total_users, icon: Users, color: 'text-acture-primary' },
      ]
    : []

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Admin Dashboard</h1>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {cards.map((card) => (
          <div key={card.label} className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">{card.label}</span>
              <card.icon className={`w-5 h-5 ${card.color}`} />
            </div>
            <p className="text-2xl font-bold text-gray-800">{card.value}</p>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="font-semibold text-gray-700 mb-3">Sync Documents</h2>
          <div className="flex gap-2">
            <button
              onClick={() => handleSync('sharepoint')}
              disabled={syncing}
              className="flex items-center gap-2 bg-acture-primary text-white px-4 py-2 rounded-lg text-sm hover:bg-acture-secondary transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
              SharePoint Sync
            </button>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="font-semibold text-gray-700 mb-3">Quick Links</h2>
          <div className="flex flex-col gap-2">
            <Link
              to="/admin/feedback"
              className="text-sm text-acture-accent hover:underline flex items-center gap-1"
            >
              <AlertCircle className="w-4 h-4" /> Review Feedback
              {stats && stats.pending_feedback > 0 && (
                <span className="ml-1 bg-acture-danger text-white text-xs rounded-full px-1.5 py-0.5">
                  {stats.pending_feedback}
                </span>
              )}
            </Link>
            <Link
              to="/admin/documents"
              className="text-sm text-acture-accent hover:underline flex items-center gap-1"
            >
              <FileText className="w-4 h-4" /> Document Index
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
