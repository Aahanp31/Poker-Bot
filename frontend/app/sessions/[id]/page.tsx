import Link from 'next/link'
import { getSessionStats, getSessionHands } from '@/lib/api'
import StatsChart from '@/components/StatsChart'

export default async function SessionPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id }  = await params
  const sessionId = Number(id)

  const [stats, hands] = await Promise.all([
    getSessionStats(sessionId),
    getSessionHands(sessionId),
  ])

  return (
    <div>
      <div className="flex items-center gap-3 mb-8">
        <Link href="/" className="text-gray-500 hover:text-white transition-colors text-sm">
          ← Sessions
        </Link>
        <span className="text-gray-700">/</span>
        <h1 className="text-2xl font-bold">Session #{sessionId}</h1>
      </div>

      <section className="mb-10">
        <h2 className="text-lg font-semibold mb-4 text-gray-300">Player Stats</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-4">
          <StatsChart stats={stats} />
        </div>
        <div className="grid grid-cols-3 gap-3">
          {stats.map(s => (
            <div key={s.player} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className="text-sm text-gray-400 mb-1">{s.player}</div>
              <div className={`text-xl font-bold ${s.total_net >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {s.total_net >= 0 ? '+' : ''}{s.total_net}
              </div>
              <div className="text-xs text-gray-500 mt-1">{s.wins} wins</div>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4 text-gray-300">Hands</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-left">
                <th className="px-4 py-3 font-medium">#</th>
                <th className="px-4 py-3 font-medium">Winner</th>
                <th className="px-4 py-3 font-medium">Pot</th>
                <th className="px-4 py-3 font-medium">Method</th>
                <th className="px-4 py-3 font-medium">Ended</th>
                <th className="px-4 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {hands.map(h => (
                <tr key={h.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                  <td className="px-4 py-3 text-gray-500">{h.hand_num}</td>
                  <td className="px-4 py-3 font-medium text-emerald-400">{h.winner}</td>
                  <td className="px-4 py-3">${h.pot}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      h.method === 'showdown'
                        ? 'bg-blue-900/50 text-blue-300'
                        : 'bg-gray-800 text-gray-400'
                    }`}>
                      {h.method}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400">{h.street}</td>
                  <td className="px-4 py-3">
                    <Link href={`/hands/${h.id}`} className="text-xs text-gray-500 hover:text-white transition-colors">
                      view →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
