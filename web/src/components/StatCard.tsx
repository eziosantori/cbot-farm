import type { ReactNode } from 'react'

type StatCardProps = {
  label: string
  value: ReactNode
  tone?: 'default' | 'accent' | 'warning'
  detail?: ReactNode
}

export default function StatCard({
  label,
  value,
  tone = 'default',
  detail,
}: StatCardProps): JSX.Element {
  return (
    <section className={`stat-card stat-card--${tone}`}>
      <p className="stat-card__label">{label}</p>
      <p className="stat-card__value">{value}</p>
      {detail ? <div className="stat-card__detail">{detail}</div> : null}
    </section>
  )
}
