import type { Metadata } from "next";
import { AppShell } from "@/components/AppShell";
import { FlashSalePage } from "@/components/FlashSalePage";
import { allProducts } from "@/lib/catalog";

export const metadata: Metadata = {
  title: "Bật Nhịp Chung Kết - Sút Cực Đại | Điện máy XANH",
  description: "Flash Sale World Cup, giảm giá điện máy và gia dụng đến 50%.",
};

export default function FlashSaleRoute() {
  return (
    <AppShell>
      <FlashSalePage products={allProducts} />
    </AppShell>
  );
}
