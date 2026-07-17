import type { ReactNode } from "react";
import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { homePageData } from "@/lib/home-data";

interface AppShellProps {
  children: ReactNode;
  showFooter?: boolean;
  showTopBanner?: boolean;
}

export function AppShell({
  children,
  showFooter = true,
  showTopBanner = true,
}: AppShellProps) {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Header categories={homePageData.categories} showTopBanner={showTopBanner} />
      <div className="page-enter flex-1">{children}</div>
      {showFooter ? <Footer supportContacts={homePageData.supportContacts} /> : null}
    </div>
  );
}
