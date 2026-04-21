export function formatTimestamp(isoString) {
  if (!isoString) return '-';
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return '-';

  const pad = (n) => String(n).padStart(2, '0');
  const exact = `${pad(date.getDate())}.${pad(date.getMonth() + 1)}.${date.getFullYear()} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;

  const diffMs = Date.now() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffH = Math.floor(diffMin / 60);
  const diffD = Math.floor(diffH / 24);

  let relative;
  if (diffSec < 60) relative = 'acum câteva secunde';
  else if (diffMin < 60) relative = `acum ${diffMin} min`;
  else if (diffH < 24) relative = `acum ${diffH} ore`;
  else if (diffD === 1) relative = 'ieri';
  else relative = `acum ${diffD} zile`;

  return `${exact} (${relative})`;
}
