import { useState, useRef, useEffect } from 'react'
import { Send, ThumbsUp, ThumbsDown, FileText, Lightbulb, PlusCircle } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { api, type ChatResponse } from '../api/client'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: { title: string; url: string }[]
  queryId?: string
  feedbackGiven?: 'positive' | 'negative' | null
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [docCount, setDocCount] = useState(0)
  const [sessionId, setSessionId] = useState<string | undefined>(undefined)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.stats().then((s) => setDocCount(s.total_documents)).catch(() => {})
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleNewChat = () => {
    setMessages([])
    setSessionId(undefined)
    setInput('')
  }

  const handleSend = async () => {
    const msg = input.trim()
    if (!msg || loading) return
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: msg }])
    setLoading(true)

    try {
      const data: ChatResponse = await api.chat(msg, sessionId)
      // Store session ID from first response for conversation continuity
      if (!sessionId) {
        setSessionId(data.session_id)
      }
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.response,
          sources: data.sources,
          queryId: data.query_id,
          feedbackGiven: null,
        },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleFeedback = async (idx: number, type: 'positive' | 'negative') => {
    const msg = messages[idx]
    if (!msg.queryId || msg.feedbackGiven) return
    try {
      await api.feedback(msg.queryId, type)
      setMessages((prev) =>
        prev.map((m, i) => (i === idx ? { ...m, feedbackGiven: type } : m)),
      )
    } catch {}
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)]">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 gap-4">
            <Lightbulb className="w-12 h-12 text-acture-accent opacity-50" />
            <h2 className="text-xl font-semibold text-gray-600">Acture Advisor</h2>
            <p className="text-sm">
              Ask questions about {docCount > 0 ? `${docCount} indexed documents` : 'your documentation'}
            </p>
            <div className="flex flex-wrap gap-2 mt-4 max-w-lg justify-center">
              {['How do I reset a password?', 'What is our VPN setup process?', 'How do I configure LAPS?'].map(
                (q) => (
                  <button
                    key={q}
                    onClick={() => {
                      setInput(q)
                    }}
                    className="text-xs bg-white border border-gray-200 rounded-full px-3 py-1.5 hover:bg-gray-50 transition-colors"
                  >
                    {q}
                  </button>
                ),
              )}
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-acture-primary text-white'
                      : 'bg-white border border-gray-200 shadow-sm'
                  }`}
                >
                  <div className="prose prose-sm max-w-none [&_p]:m-0 [&_ul]:mt-1 [&_ol]:mt-1">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>

                  {/* Sources */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-gray-100">
                      <p className="text-xs font-medium text-gray-500 mb-1">Sources</p>
                      <div className="space-y-1">
                        {msg.sources.slice(0, 3).map((s, si) => (
                          <a
                            key={si}
                            href={s.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1.5 text-xs text-acture-accent hover:underline"
                          >
                            <FileText className="w-3 h-3 shrink-0" />
                            <span className="truncate">{s.title}</span>
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Feedback */}
                  {msg.role === 'assistant' && msg.queryId && (
                    <div className="mt-2 flex gap-2">
                      <button
                        onClick={() => handleFeedback(idx, 'positive')}
                        disabled={!!msg.feedbackGiven}
                        className={`p-1 rounded transition-colors ${
                          msg.feedbackGiven === 'positive'
                            ? 'text-acture-success'
                            : 'text-gray-300 hover:text-acture-success'
                        }`}
                      >
                        <ThumbsUp className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleFeedback(idx, 'negative')}
                        disabled={!!msg.feedbackGiven}
                        className={`p-1 rounded transition-colors ${
                          msg.feedbackGiven === 'negative'
                            ? 'text-acture-danger'
                            : 'text-gray-300 hover:text-acture-danger'
                        }`}
                      >
                        <ThumbsDown className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-gray-200 bg-white px-4 py-3">
        <div className="max-w-3xl mx-auto flex gap-2">
          {messages.length > 0 && (
            <button
              onClick={handleNewChat}
              title="New conversation"
              className="rounded-full border border-gray-300 text-gray-500 p-2.5 hover:bg-gray-50 transition-colors"
            >
              <PlusCircle className="w-4 h-4" />
            </button>
          )}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask a question about your documentation..."
            className="flex-1 rounded-full border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-acture-accent focus:border-transparent"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="rounded-full bg-acture-primary text-white p-2.5 hover:bg-acture-secondary transition-colors disabled:opacity-40"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
