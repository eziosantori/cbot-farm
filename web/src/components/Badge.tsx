type BadgeProps = {
  label: string
  tone?: 'neutral' | 'accent' | 'success' | 'warning'
}

export default function Badge({ label, tone = 'neutral' }: BadgeProps): JSX.Element {
  return <span className={`badge badge--${tone}`}>{label}</span>
}
