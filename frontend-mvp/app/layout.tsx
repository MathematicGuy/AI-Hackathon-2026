import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Tư vấn máy lạnh — MVP test",
  description: "Frontend thử nghiệm luồng tư vấn máy lạnh (mock data).",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
