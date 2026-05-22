'use client'

import { useEffect, useState } from 'react'
import { getSessions, runSession, type Session, type RunConfig } from '@/lib/api'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router  = useRouter()
  const [sessions, setSessions] = useState<Session[]>([])
  const [showModal, setShowModal] = useState(false)
  const [running, setRunning]   = useState(false)
  const [config, setConfig]     = useState<RunConfig>({
    num_players:    3,
    big_blind:      20,
    num_hands:      50,
    starting_stack: 1000,
  })

  useEffect(() => {
    getSessions().then(setSessions).catch(console.error)
  }, [])

  async function handleRun() {
    setRunning(true)
    try {
      const { session_id } = await runSession(config)
      router.push(`/sessions/${session_id}`)
    } finally {
      setRunning(false)
      setShowModal(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold">Sessions</h1>
        <button
          onClick={() => setShowModal(true)}
          className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          Run Session
        </button>
      </div>

      {sessions.length === 0 ? (
        <p className="text-gray-500">No sessions yet. Run one to get started.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {sessions.map(s => (
            <a
              key={s.id}
              href={`/sessions/${s.id}`}
              className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-emerald-700 transition-colors"
            >
              <div className="text-xs text-gray-500 mb-2">
                {new Date(s.started_at).toLocaleString()}
              </div>
              <div className="text-lg font-semibold mb-3">Session #{s.id}</div>
              <div className="flex gap-4 text-sm text-gray-400">
                <span>{s.hand_count} hands</span>
                <span>{s.num_players} players</span>
                <span>BB ${s.big_blind}</span>
              </div>
            </a>
          ))}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-sm">
            <h2 className="text-xl font-bold mb-5">Run Session</h2>

            {[
              { label: 'Players',        key: 'num_players'    as const, min: 2, max: 9 },
              { label: 'Big Blind',      key: 'big_blind'      as const, min: 2          },
              { label: 'Hands',          key: 'num_hands'      as const, min: 1          },
              { label: 'Starting Stack', key: 'starting_stack' as const, min: 100        },
            ].map(({ label, key, min, max }) => (
              <div key={key} className="mb-4">
                <label className="block text-sm text-gray-400 mb-1">{label}</label>
                <input
                  type="number"
                  min={min}
                  max={max}
                  value={config[key]}
                  onChange={e => setConfig(c => ({ ...c, [key]: Number(e.target.value) }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
                />
              </div>
            ))}

            <div className="flex gap-3 mt-6">
              <button
                onClick={handleRun}
                disabled={running}
                className="flex-1 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white py-2 rounded-lg font-medium transition-colors"
              >
                {running ? 'Running…' : 'Run'}
              </button>
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 bg-gray-800 hover:bg-gray-700 text-white py-2 rounded-lg font-medium transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
