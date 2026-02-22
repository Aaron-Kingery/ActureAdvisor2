import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, ThumbsUp, ThumbsDown } from 'lucide-react'
import { api, type FeedbackItem } from '../api/client'

export default function Feedback() {
  const [items, setItems] = useState<FeedbackItem[]>([])
  const [selected, setSelected] = useState<FeedbackItem | null>(null)
  const [notes, setNotes] = useState('')

  useEffect(() => {
    api.feedbackList().then(setItems).catch(() => {})
  }, [])

  const handleUpdate = async (status: string) => {
    if (!selected) return
    try {
      const updated = await api.updateFeedback(selected.id, status, notes)
      setItems((prev) => prev.map((i) => (i.id === selected.id ? { ...i, ...updated } : i)))
      setSelected({ ...selected, ...updated })
    } catch {}
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Link to="/admin" className="text-gray-400 hover:text-gray-600">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-2xl font-bold text-gray-800">Feedback Review</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* List */}
        <div className="space-y-2 max-h-[70vh] overflow-y-auto">
          {items.length === 0 && <p className="text-gray-400 text-sm">No feedback items yet.</p>}
          {items.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setSelected(item)
                setNotes(item.admin_notes || '')
              }}
              className={`w-full text-left p-3 rounded-lg border transition-colors ${
                selected?.id === item.id
                  ? 'border-acture-accent bg-blue-50'
                  : 'border-gray-200 bg-white hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  {item.feedback_type === 'positive' ? (
                    <ThumbsUp className="w-4 h-4 text-acture-success" />
                  ) : (
                    <ThumbsDown className="w-4 h-4 text-acture-danger" />
                  )}
                  <span className="text-xs text-gray-500">{item.user_email || 'Unknown'}</span>
                </div>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    item.status === 'new'
                      ? 'bg-yellow-100 text-yellow-800'
                      : item.status === 'resolved'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-blue-100 text-blue-800'
                  }`}
                >
                  {item.status}
                </span>
              </div>
              <p className="text-sm text-gray-700 truncate">{item.query_text || 'No query text'}</p>
            </button>
          ))}
        </div>

        {/* Detail */}
        {selected && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-3">Feedback Detail</h3>
            <div className="space-y-3 text-sm">
              <div>
                <span className="font-medium text-gray-500">Query:</span>
                <p className="mt-1 text-gray-700">{selected.query_text}</p>
              </div>
              <div>
                <span className="font-medium text-gray-500">Response:</span>
                <p className="mt-1 text-gray-700 text-xs max-h-32 overflow-y-auto">
                  {selected.query_response}
                </p>
              </div>
              <div>
                <label className="font-medium text-gray-500">Admin Notes</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className="mt-1 w-full border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-acture-accent focus:border-transparent"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleUpdate('in_review')}
                  className="bg-acture-accent text-white px-3 py-1.5 rounded-lg text-xs hover:bg-blue-600"
                >
                  Mark In Review
                </button>
                <button
                  onClick={() => handleUpdate('resolved')}
                  className="bg-acture-success text-white px-3 py-1.5 rounded-lg text-xs hover:bg-green-700"
                >
                  Resolve
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
