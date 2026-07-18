import type { Metadata } from "next";
import { AccountOrdersScreen } from "@/components/AccountOrdersScreen";
import { AppShell } from "@/components/AppShell";
import { allProducts } from "@/lib/catalog";

export const metadata: Metadata = {
  title: "Đơn hàng đã mua | Điện máy XANH",
};

export default function PurchaseHistoryPage() {
  return (
    <AppShell showFooter={false} showTopBanner={false}>
      <AccountOrdersScreen products={allProducts.slice(0, 4)} />
    </AppShell>
  );
}
