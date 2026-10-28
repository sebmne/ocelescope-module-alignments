/** What the backend said went wrong (its `detail`), or a fallback. */
export function errorMessage(error: unknown, fallback: string): string {
  const detail = (error as { response?: { data?: { detail?: unknown } } } | null)?.response?.data
    ?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && typeof detail[0]?.msg === "string") return detail[0].msg;
  return fallback;
}
