import type { Metadata } from "next";
import { AppShell } from "@/components/AppShell";
import { CartScreen } from "@/components/CartScreen";

export const metadata: Metadata = {
  title: "Giỏ hàng | Điện máy XANH",
};

export default function CartPage() {
  return (
    <AppShell showFooter={false}>
      <main className="min-h-[calc(100vh-175px)] bg-[#f3f4f6] px-3 py-6 md:px-4 md:py-10">
        <CartScreen />
      </main>
    </AppShell>
  );
}
