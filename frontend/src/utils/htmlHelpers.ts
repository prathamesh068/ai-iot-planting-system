// ── Date helpers ──────────────────────────────────────────────────────────

/**
 * Parses a date value string like `Date(2024,0,15,10,30,0)`
 * (month is 0-indexed) into a JS Date. Falls back to `new Date(v)` for
 * plain ISO / formatted strings.
 */
export function parseDateValue(v: string): Date | null {
  if (!v) return null;
  const m = /^Date\((\d+),(\d+),(\d+)(?:,(\d+),(\d+),(\d+))?\)$/.exec(v.trim());
  if (m) {
    const [, yr, mo, dy, hh = '0', mm = '0', ss = '0'] = m;
    return new Date(+yr, +mo, +dy, +hh, +mm, +ss);
  }
  const d = new Date(v);
  return isNaN(d.getTime()) ? null : d;
}

const HUMAN_DATE_FORMATTER = new Intl.DateTimeFormat('en-GB', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
  hour12: true,
});

function formatHumanReadableDate(v: string): string {
  const d = parseDateValue(v);
  if (!d) return v || '—';

  // Intl gives lowercase am/pm in some environments; normalize to AM/PM.
  return HUMAN_DATE_FORMATTER.format(d).replace(/\b(am|pm)\b/i, (m) => m.toUpperCase());
}

/** Full format for table: "10 Mar 2026, 2:10 PM" */
export function formatDateFull(v: string): string {
  return formatHumanReadableDate(v);
}

/** Chart format uses same readable timestamp style */
export function formatDateShort(v: string): string {
  const d = parseDateValue(v);
  if (!d) return v || '';
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `${hh}:${mm}`;
}

// ── HTML helpers ──────────────────────────────────────────────────────────

export function escHtml(s: string): string {
  return String(s)
    .replace(/&/g, '&' + 'amp;')
    .replace(/</g, '&' + 'lt;')
    .replace(/>/g, '&' + 'gt;')
    .replace(/"/g, '&' + 'quot;');
}

export function syntaxHighlightJson(raw: string): string {
  // Strip markdown code fences if present
  let text = raw
    .replace(/^```json\s*/i, '')
    .replace(/^```\s*/i, '')
    .replace(/```\s*$/, '')
    .trim();

  // Try to pretty-print valid JSON
  try {
    text = JSON.stringify(JSON.parse(text), null, 2);
  } catch {
    // Not valid JSON — display as-is
  }

  // Syntax colour via HTML spans
  return escHtml(text).replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    (m) => {
      if (/^"/.test(m)) {
        return /:$/.test(m)
          ? `<span class="key">${m}</span>`
          : `<span class="str">${m}</span>`;
      }
      if (/true|false/.test(m)) return `<span class="bool">${m}</span>`;
      if (/null/.test(m)) return `<span class="bool">${m}</span>`;
      return `<span class="num">${m}</span>`;
    }
  );
}
