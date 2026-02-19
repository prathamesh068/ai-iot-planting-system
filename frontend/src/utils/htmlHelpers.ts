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
