import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { UtilityServiceScreen } from "@/components/UtilityServiceScreen";
import { getServiceMenuItem, serviceMenuItems } from "@/lib/mega-menu-data";

interface UtilityPageProps {
  params: Promise<{ slug: string }>;
}

export function generateStaticParams() {
  return serviceMenuItems.map((item) => ({
    slug: item.href.split("/").filter(Boolean).at(-1) || item.id,
  }));
}

export async function generateMetadata({ params }: UtilityPageProps): Promise<Metadata> {
  const { slug } = await params;
  const item = getServiceMenuItem(slug);
  return {
    title: item ? `${item.label} | Điện máy XANH` : "Dịch vụ tiện ích | Điện máy XANH",
  };
}

export default async function UtilityPage({ params }: UtilityPageProps) {
  const { slug } = await params;
  const item = getServiceMenuItem(slug);
  if (!item) {
    notFound();
  }

  return (
    <AppShell>
      <UtilityServiceScreen item={item} />
    </AppShell>
  );
}
