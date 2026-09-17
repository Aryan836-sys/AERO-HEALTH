export function formatTime(date: string, language = 'en'): string {
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime()))
    return '\u2014';
  return new Intl.DateTimeFormat(language === 'ne' ? 'ne-NP' : 'en-GB', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kathmandu' }).format(parsed);
}
export function formatDate(date: string, language = 'en'): string {
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime()))
    return '\u2014';
  return new Intl.DateTimeFormat(language === 'ne' ? 'ne-NP' : 'en-GB', { day: 'numeric', month: 'short', timeZone: 'Asia/Kathmandu' }).format(parsed);
}
export function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]!);
}
export function csvCell(value: string | number | null): string {
  let text = String(value ?? '');
  if (/^[=+@\-\t\r]/.test(text))
    text = "'" + text;
  return '"' + text.replace(/"/g, '""') + '"';
}
export function downloadCsv(filename: string, rows: (string | number | null)[][]): void {
  const content = '\ufeff' + rows.map((row) => row.map(csvCell).join(',')).join('\r\n');
  const url = URL.createObjectURL(new Blob([content], { type: 'text/csv;charset=utf-8;' }));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.';
}
