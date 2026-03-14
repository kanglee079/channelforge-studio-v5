
import { ReactNode } from 'react'

export default function Card({ title, children, right }: { title: string, children: ReactNode, right?: ReactNode }) {
  return (
    <section className="card">
      <div className="card-head">
        <h3>{title}</h3>
        {right}
      </div>
      <div>{children}</div>
    </section>
  )
}
