const BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (res.status === 401) {
    window.location.href = '/auth/login?returnTo=' + encodeURIComponent(window.location.pathname)
    throw new Error('Unauthorized')
  }
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export interface ChatResponse {
  response: string
  sources: { title: string; url: string }[]
  query_id: string
  session_id: string
}

export interface Stats {
  total_queries: number
  total_documents: number
  pending_feedback: number
  total_users: number
  success_rate: number
}

export interface FeedbackItem {
  id: string
  query_id: string
  feedback_type: string
  status: string
  admin_notes: string | null
  created_at: string
  query_text?: string
  query_response?: string
  user_email?: string
}

export interface DocumentItem {
  id: string
  title: string
  file_type: string
  source_url: string
  last_synced: string
}

export const api = {
  chat: (message: string, sessionId?: string) =>
    request<ChatResponse>('/chat/', {
      method: 'POST',
      body: JSON.stringify({ message, session_id: sessionId }),
    }),

  feedback: (queryId: string, feedbackType: string) =>
    request<{ status: string }>(`/chat/${queryId}/feedback`, {
      method: 'POST',
      body: JSON.stringify({ feedback_type: feedbackType }),
    }),

  stats: () => request<Stats>('/admin/stats'),

  feedbackList: () => request<FeedbackItem[]>('/admin/feedback'),

  updateFeedback: (id: string, status: string, notes: string) =>
    request<FeedbackItem>(`/admin/feedback/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status, admin_notes: notes }),
    }),

  syncTrigger: (connector: string) =>
    request<{ status: string; message: string }>(`/sync/trigger?connector=${connector}`, {
      method: 'POST',
    }),

  documents: () => request<DocumentItem[]>('/admin/documents'),
}
