import { useState } from 'react'

interface Card {
  letter: string
  title: string
  body: string
}

const CARDS: Card[] = [
  {
    letter: 'A · Tighter',
    title: '85 → 110mm, same angle.',
    body: 'Squeezes background. Less cue, more face.',
  },
  {
    letter: 'B · Lower angle',
    title: 'Camera 1.2m high, subject looms.',
    body: 'Stairs silhouettes in BG.',
  },
  {
    letter: 'C · Split comp.',
    title: 'Doorway in 4th-left, actor off-center right.',
    body: 'Implies choice.',
  },
]

export default function OptionCards() {
  const [selected, setSelected] = useState<string | null>(null)

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginTop: 10 }}>
      {CARDS.map((card) => {
        const isSelected = selected === card.letter
        return (
          <button
            key={card.letter}
            onClick={() => setSelected(isSelected ? null : card.letter)}
            style={{
              background: isSelected ? 'rgba(91,127,255,0.10)' : 'rgba(255,255,255,0.02)',
              border: isSelected ? '1px solid var(--accent)' : '1px solid var(--border)',
              borderRadius: 'var(--radius-md)',
              padding: '8px 10px',
              textAlign: 'left',
              cursor: 'pointer',
              transition: 'border-color 0.15s, background 0.15s',
            }}
          >
            {/* Thumbnail placeholder */}
            <div
              style={{
                height: 36,
                background: isSelected ? 'rgba(91,127,255,0.08)' : 'rgba(255,255,255,0.02)',
                borderRadius: 4,
                marginBottom: 7,
                border: `1px solid ${isSelected ? 'rgba(91,127,255,0.2)' : 'var(--border)'}`,
              }}
            />
            <div style={{ fontSize: 10, fontWeight: 700, color: isSelected ? 'var(--accent2)' : 'var(--accent)', marginBottom: 3 }}>
              {card.letter}
            </div>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text)', marginBottom: 2 }}>
              {card.title}
            </div>
            <div style={{ fontSize: 10, color: 'var(--muted)' }}>{card.body}</div>
          </button>
        )
      })}
    </div>
  )
}
