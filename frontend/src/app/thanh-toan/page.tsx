import type { Metadata } from "next";
import { AppShell } from "@/components/AppShell";
import { CheckoutScreen } from "@/components/CheckoutScreen";

export const metadata: Metadata = {
  title: "Thanh toán | Điện máy XANH",
};

export default function CheckoutPage() {
  return (
    <AppShell showFooter={false}>
      <main className="min-h-[calc(100vh-175px)] bg-[#f3f4f6] px-3 py-6 md:px-4 md:py-10">
        <CheckoutScreen />
      </main>
    </AppShell>
  );
}
