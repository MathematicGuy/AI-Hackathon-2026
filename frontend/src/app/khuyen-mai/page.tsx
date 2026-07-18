import type { Metadata } from "next";
import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { SafeImage } from "@/components/SafeImage";
import { getArticleSlug, getCampaignSlug } from "@/lib/catalog";
import { formatDate } from "@/lib/format";
import { homePageData } from "@/lib/home-data";

export const metadata: Metadata = {
  title: "Khuyến mãi | Điện máy XANH",
  description: "Tin khuyến mãi và chương trình ưu đãi nổi bật.",
};

export default function PromotionsPage() {
  return (
    <AppShell>
      <main className="mx-auto w-full max-w-[1200px] px-3 py-5 md:px-4">
        <Breadcrumbs items={[{ label: "Trang chủ", href: "/" }, { label: "Khuyến mãi" }]} />
        <div className="mt-4 rounded-xl bg-[linear-gradient(115deg,#126ed4,#42b8f5)] p-6 text-white md:p-8">
          <p className="text-sm font-bold text-brand-yellow">TIN MỚI MỖI NGÀY</p>
          <h1 className="mt-1 text-2xl font-bold md:text-3xl">Khuyến mãi Điện máy XANH</h1>
          <p className="mt-2 text-sm text-white/85">Tổng hợp chương trình ưu đãi và chính sách nổi bật mới nhất.</p>
        </div>

        <section className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {homePageData.articles.map((article) => (
            <Link
              key={article.id}
              href={`/khuyen-mai/${getArticleSlug(article)}`}
              className="group overflow-hidden rounded-xl bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md active:translate-y-0"
            >
              <SafeImage
                src={article.src}
                alt={article.name}
                className="aspect-[16/9] w-full object-cover transition group-hover:scale-[1.02]"
                fallbackLabel={article.name}
              />
              <div className="p-4">
                <p className="text-xs font-bold uppercase text-brand-blue">{article.sub}</p>
                <h2 className="mt-2 line-clamp-2 text-base font-bold leading-6 text-slate-900 group-hover:text-brand-blue">
                  {article.name}
                </h2>
                {article.publishedAt ? (
                  <time className="mt-3 block text-xs text-slate-400" dateTime={article.publishedAt}>
                    {formatDate(article.publishedAt)}
                  </time>
                ) : null}
              </div>
            </Link>
          ))}
        </section>

        <section className="mt-4 rounded-xl bg-white p-4 shadow-sm">
          <h2 className="text-xl font-bold text-slate-900">Gian hàng ưu đãi</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {homePageData.weeklyBanners.map((banner) => (
              <Link
                key={banner.id}
                href={`/khuyen-mai/${getCampaignSlug(banner)}`}
                className="overflow-hidden rounded-lg border border-slate-100 transition hover:shadow-md"
              >
                <SafeImage
                  src={banner.src}
                  alt={banner.title}
                  className="aspect-[16/7] w-full object-cover"
                  fallbackLabel={banner.title}
                />
              </Link>
            ))}
          </div>
        </section>
      </main>
    </AppShell>
  );
}
