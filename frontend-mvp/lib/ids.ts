export function generateId(prefix: string): string {
  return `${prefix}_${crypto.randomUUID()}`;
}

export function ensureSessionId(id?: string): string {
  return id && id.length > 0 ? id : generateId("sess");
}

export function ensureRequestId(id?: string): string {
  return id && id.length > 0 ? id : generateId("req");
}
