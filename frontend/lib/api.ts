const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export interface Session {
  id:          number
  started_at:  string
  num_players: number
  big_blind:   number
  hand_count:  number
}

export interface PlayerStat {
  player:    string
  wins:      number
  total_net: number
}

export interface Hand {
  id:         number
  session_id: number
  hand_num:   number
  winner:     string
  pot:        number
  method:     string
  street:     string
}

export interface Action {
  id:     number
  hand_id: number
  player: string
  street: string
  action: string
  amount: number
}

export interface RunConfig {
  num_players:    number
  big_blind:      number
  num_hands:      number
  starting_stack: number
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`)
  if (!res.ok) throw new Error(`${res.status} ${path}`)
  return res.json()
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`${res.status} ${path}`)
  return res.json()
}

export const getSessions     = ()        => get<Session[]>   ('/api/sessions')
export const getSessionStats = (id: number) => get<PlayerStat[]>(`/api/sessions/${id}/stats`)
export const getSessionHands = (id: number) => get<Hand[]>      (`/api/sessions/${id}/hands`)
export const getHandActions  = (id: number) => get<Action[]>    (`/api/hands/${id}/actions`)
export const runSession      = (cfg: RunConfig) => post<{ session_id: number }>('/api/run', cfg)
