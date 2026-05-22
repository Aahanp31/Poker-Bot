'use client'

import { BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer } from 'recharts'
import type { PlayerStat } from '@/lib/api'

export default function StatsChart({ stats }: { stats: PlayerStat[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={stats} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <XAxis dataKey="player" stroke="#6b7280" tick={{ fill: '#9ca3af' }} />
        <YAxis stroke="#6b7280" tick={{ fill: '#9ca3af' }} />
        <Tooltip
          contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }}
          labelStyle={{ color: '#f3f4f6' }}
        />
        <Bar dataKey="total_net" radius={[4, 4, 0, 0]}>
          {stats.map((s, i) => (
            <Cell key={i} fill={s.total_net >= 0 ? '#10b981' : '#ef4444'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
