import Link from 'next/link'
import { getHandActions } from '@/lib/api'

const ACTION_COLORS: Record<string, string> = {
  fold:  'bg-red-900/50 text-red-300',
  check: 'bg-gray-800 text-gray-300',
  call:  'bg-blue-900/50 text-blue-300',
  raise: 'bg-amber-900/50 text-amber-300',
}

const STREET_ORDER = ['preflop', 'flop', 'turn', 'river']

export default async function HandPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const handId = Number(id)
  const actions = await getHandActions(handId)

  const byStreet = STREET_ORDER.map(street => ({
    street,
    actions: actions.filter(a => a.street === street),
  })).filter(g => g.actions.length > 0)

  return (
    <div>
      <div className="flex items-center gap-3 mb-8">
        <button onClick={() => history.back()} className="text-gray-500 hover:text-white transition-colors text-sm">
          ← Back
        </button>
        <span className="text-gray-700">/</span>
        <h1 className="text-2xl font-bold">Hand #{handId}</h1>
      </div>

      {byStreet.length === 0 ? (
        <p className="text-gray-500">No actions recorded for this hand.</p>
      ) : (
        <div className="space-y-6">
          {byStreet.map(({ street, actions: streetActions }) => (
            <section key={street}>
              <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-3">
                {street}
              </h2>
              <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-800 text-gray-500 text-left">
                      <th className="px-4 py-3 font-medium">Player</th>
                      <th className="px-4 py-3 font-medium">Action</th>
                      <th className="px-4 py-3 font-medium">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {streetActions.map(a => (
                      <tr key={a.id} className="border-b border-gray-800/50">
                        <td className="px-4 py-3 font-medium">{a.player}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${ACTION_COLORS[a.action] ?? 'bg-gray-800 text-gray-400'}`}>
                            {a.action}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-gray-400">
                          {a.amount > 0 ? `$${a.amount}` : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  )
}
