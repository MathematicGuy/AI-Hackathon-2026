export function display(v: string | number | null | undefined): string {
  if (v === null || v === undefined || v === "") return "không có";
  return String(v);
}

export function formatVnd(v: number | null | undefined): string {
  if (v === null || v === undefined) return "chưa rõ";
  return `${v.toLocaleString("vi-VN")}₫`;
}
