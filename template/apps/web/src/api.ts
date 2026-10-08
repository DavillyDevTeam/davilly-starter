export function apiUrl(
  path: string,
  base: string = import.meta.env.VITE_API_URL ?? '',
): string {
  return `${base.replace(/\/+$/, '')}${path}`;
}
