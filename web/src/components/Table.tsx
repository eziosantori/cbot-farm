import type { TableColumn } from '../types'

type TableProps<T> = {
  columns: TableColumn<T>[]
  rows: T[]
  emptyLabel?: string
}

export default function Table<T extends Record<string, unknown>>({
  columns,
  rows,
  emptyLabel = 'No data'
}: TableProps<T>): JSX.Element {
  if (!rows.length) {
    return <p>{emptyLabel}</p>
  }

  return (
    <table>
      <thead>
        <tr>
          {columns.map((col) => (
            <th key={col.key}>{col.label}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, idx) => (
          <tr key={idx}>
            {columns.map((col) => (
              <td key={col.key}>{col.render ? col.render(row) : String(row[col.key] ?? '-')}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
