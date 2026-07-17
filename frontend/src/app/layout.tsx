import type { Metadata } from "next";
import { CartProvider } from "@/components/CartProvider";
import { ChatbotAssistant } from "@/components/ChatbotAssistant";
import { ToastProvider } from "@/components/ToastProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Điện máy XANH",
  description:
    "Mua sắm điện máy, điện lạnh và gia dụng với nhiều ưu đãi tại Điện máy XANH.",
  icons: {
    icon: "/icon.svg",
    shortcut: "/icon.svg",
    apple: "/icon.svg",
  },
  formatDetection: {
    address: false,
    email: false,
    telephone: false,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" className="h-full antialiased" suppressHydrationWarning>
      <body
        className="min-h-full flex flex-col"
        suppressHydrationWarning
      >
        <ToastProvider>
          <CartProvider>
            {children}
            <ChatbotAssistant />
          </CartProvider>
        </ToastProvider>
      </body>
    </html>
  );
}
