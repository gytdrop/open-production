import { useState } from 'react'

export default function CommandBar() {
  const [value, setValue]   = useState('')
  const [lastSent, setLastSent] = useState<string | null>(null)
  const [focused, setFocused]   = useState(false)

  function handleSend() {
    const cmd = value.trim()
    if (!cmd) return
    setLastSent(cmd)
    setValue('')
    setTimeout(() => setLastSent(null), 3000)
  }

  return (
    <div
      style={{
        padding: '8px 14px 10px',
        flexShrink: 0,
        borderTop: '1px solid var(--border)',
      }}
    >
      {/* Input row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          background: focused ? 'rgba(255,255,255,0.045)' : 'rgba(255,255,255,0.025)',
          border: `1px solid ${focused ? 'rgba(91,127,255,0.45)' : 'rgba(91,127,255,0.2)'}`,
          borderRadius: 'var(--radius-md)',
          padding: '0 8px 0 12px',
          transition: 'border-color 0.2s, background 0.2s',
        }}
      >
        {/* Prompt glyph */}
        <span
          style={{
            fontSize: 12,
            color: focused ? 'var(--accent)' : 'var(--dim)',
            flexShrink: 0,
            fontFamily: 'monospace',
            transition: 'color 0.2s',
            userSelect: 'none',
          }}
        >
          ›
        </span>
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder="Ask the crew anything — type ⌘K for commands…"
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            color: 'var(--text)',
            fontSize: 12,
            padding: '9px 0',
            letterSpacing: '0.01em',
          }}
        />
        {value.trim() && (
          <kbd
            style={{
              fontSize: 9,
              color: 'var(--dim)',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--border2)',
              borderRadius: 3,
              padding: '1px 5px',
              flexShrink: 0,
              fontFamily: 'inherit',
            }}
          >
            ↵
          </kbd>
        )}
        <button
          onClick={handleSend}
          disabled={!value.trim()}
          style={{
            padding: '5px 14px',
            fontSize: 11,
            fontWeight: 700,
            background: value.trim()
              ? 'linear-gradient(135deg, var(--accent) 0%, #4a6ee0 100%)'
              : 'rgba(91,127,255,0.15)',
            color: value.trim() ? '#fff' : 'var(--dim)',
            border: 'none',
            borderRadius: 'var(--radius-sm)',
            flexShrink: 0,
            cursor: value.trim() ? 'pointer' : 'default',
            transition: 'all 0.15s',
            letterSpacing: '0.02em',
          }}
        >
          Send
        </button>
      </div>

      {/* Status / hint row */}
      <div
        style={{
          fontSize: 10,
          color: 'var(--dim)',
          marginTop: 5,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
        }}
      >
        {lastSent ? (
          <span style={{ color: 'var(--accent2)', fontStyle: 'italic' }}>
            → sent: "{lastSent.slice(0, 50)}{lastSent.length > 50 ? '…' : ''}"
          </span>
        ) : (
          <span style={{ fontStyle: 'italic' }}>
            Try: "ask review to recheck S07" · "branch the cut darker" · "lock shot 7"
          </span>
        )}
      </div>
    </div>
  )
}
