import type { Metadata } from "next";
import { AppShell } from "@/components/AppShell";
import { LoginScreen } from "@/components/LoginScreen";

export const metadata: Metadata = {
  title: "Lịch sử mua hàng | Điện máy XANH",
};

export default function LoginPage() {
  return (
    <AppShell>
      <main className="min-h-[680px] bg-[#f3f5f9] px-3 py-10 md:px-4 md:py-16">
        <LoginScreen />
      </main>
    </AppShell>
  );
}
