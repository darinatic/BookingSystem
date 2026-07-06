// Slot times are stored as UTC (timestamptz). We render them in UTC so the demo
// always shows the seeded clinic hours (09:00–16:00) regardless of the viewer.
const dayFmt = new Intl.DateTimeFormat('en-SG', {
  weekday: 'short',
  day: 'numeric',
  month: 'short',
  timeZone: 'UTC',
})
const timeFmt = new Intl.DateTimeFormat('en-SG', {
  hour: 'numeric',
  minute: '2-digit',
  hour12: true,
  timeZone: 'UTC',
})

export const formatDay = (iso: string) => dayFmt.format(new Date(iso))
export const formatTime = (iso: string) => timeFmt.format(new Date(iso))
export const dayKey = (iso: string) => iso.slice(0, 10)
