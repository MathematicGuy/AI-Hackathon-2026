import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { SafeImage } from "@/components/SafeImage";
import {
  getArticleSlug,
  getCampaignBySlug,
  getCampaignSlug,
} from "@/lib/catalog";
import { formatDateTime } from "@/lib/format";
import { homePageData } from "@/lib/home-data";

interface PromotionPageProps {
  params: Promise<{ slug: string }>;
}

export function generateStaticParams() {
  return [
    ...homePageData.articles.map((item) => ({ slug: getArticleSlug(item) })),
    ...homePageData.weeklyBanners.map((item) => ({ slug: getCampaignSlug(item) })),
    ...homePageData.heroSlides.map((item) => ({ slug: getCampaignSlug(item) })),
  ];
}

export async function generateMetadata({ params }: PromotionPageProps): Promise<Metadata> {
  const { slug } = await params;
  const campaign = getCampaignBySlug(slug);
  return {
    title: campaign ? `${campaign.title} | Điện máy XANH` : "Khuyến mãi | Điện máy XANH",
    description: campaign?.description,
  };
}

export default async function PromotionDetailPage({ params }: PromotionPageProps) {
  const { slug } = await params;
  const campaign = getCampaignBySlug(slug);

  if (!campaign) {
    notFound();
  }

  const isWorldCup = campaign.id === "article-1" || slug === "online-only";

  return (
    <AppShell>
      <main className="mx-auto w-full max-w-[1200px] px-3 py-5 md:px-4">
        <Breadcrumbs
          items={[
            { label: "Trang chủ", href: "/" },
            { label: "Khuyến mãi", href: "/khuyen-mai" },
            { label: campaign.title },
          ]}
        />

        <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,820px)_320px]">
          <article className="rounded-xl bg-white p-4 shadow-sm md:p-6">
            <h1 className="text-2xl font-bold leading-tight text-slate-950 md:text-[30px]">
              {campaign.title}
            </h1>
            <p className="mt-3 border-b border-slate-200 pb-4 text-sm text-slate-400">
              {campaign.publishedAt
                ? `Đăng lúc ${formatDateTime(campaign.publishedAt)}`
                : "Chương trình đang được cập nhật"}
              {" • 156 lượt xem"}
            </p>
            <p className="mt-5 text-[17px] font-semibold leading-7 text-slate-800">
              {campaign.description}
            </p>
            <SafeImage
              src={campaign.src}
              alt={campaign.title}
              className="mt-5 max-h-[620px] w-full rounded-lg object-contain"
              fallbackLabel={campaign.title}
            />

            {isWorldCup ? (
              <div className="mt-6 space-y-6 text-[16px] leading-7 text-slate-700">
                <section>
                  <h2 className="text-xl font-bold text-slate-950">1. Thời gian khuyến mãi</h2>
                  <p className="mt-2">Chương trình diễn ra duy nhất từ ngày 17/07 đến hết ngày 19/07/2026.</p>
                </section>
                <section>
                  <h2 className="text-xl font-bold text-slate-950">2. Nội dung chương trình</h2>
                  <p className="mt-2">
                    Khách hàng truy cập website có thể săn Flash Sale giá sốc và tham gia quay số may mắn với sản phẩm giá 0 đồng.
                  </p>
                  <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200">
                    <table className="min-w-[620px] w-full border-collapse text-left text-sm">
                      <thead className="bg-sky-50 text-slate-800">
                        <tr>
                          <th className="border-b p-3">Thời gian</th>
                          <th className="border-b p-3">Tên sản phẩm</th>
                          <th className="border-b p-3">Giá khuyến mãi</th>
                          <th className="border-b p-3">Số lượng</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td className="border-b p-3">17/07 - 19/07</td>
                          <td className="border-b p-3">Chảo chống dính vân đá Elmich</td>
                          <td className="border-b p-3 font-bold text-[#d70018]">10.000đ</td>
                          <td className="border-b p-3">180 suất</td>
                        </tr>
                        <tr>
                          <td className="p-3">17/07 - 19/07</td>
                          <td className="p-3">Bộ 3 hộp nhựa Hokkaido</td>
                          <td className="p-3 font-bold text-[#d70018]">10.000đ</td>
                          <td className="p-3">120 suất</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </section>
                <section>
                  <h2 className="text-xl font-bold text-slate-950">3. Cách thức tham gia và quy định</h2>
                  <ul className="mt-2 list-disc space-y-2 pl-5">
                    <li>Mỗi số điện thoại chỉ được trúng một giải trong suốt chương trình.</li>
                    <li>Danh sách trúng thưởng được công bố trong vòng 5 ngày sau khi kết thúc.</li>
                    <li>Khách hàng mang theo CCCD khi nhận giải và hoàn tất thủ tục đúng hạn.</li>
                  </ul>
                </section>
              </div>
            ) : (
              <div className="mt-6 space-y-5 text-[16px] leading-7 text-slate-700">
                <h2 className="text-xl font-bold text-slate-950">Thông tin chương trình</h2>
                <p>
                  Ưu đãi áp dụng cho sản phẩm và khu vực đủ điều kiện trong thời gian diễn ra chương trình. Số lượng quà tặng có hạn và có thể kết thúc sớm.
                </p>
                <h2 className="text-xl font-bold text-slate-950">Cách tham gia</h2>
                <p>
                  Chọn sản phẩm, thêm vào giỏ hàng và hoàn tất thông tin nhận hàng. Giá cuối cùng được hiển thị trong bước thanh toán.
                </p>
              </div>
            )}
          </article>

          <aside className="h-fit rounded-xl bg-white p-4 shadow-sm">
            <h2 className="border-b border-slate-200 pb-3 text-lg font-bold text-slate-900">
              Các tin khuyến mãi khác
            </h2>
            <div className="divide-y divide-slate-100">
              {homePageData.articles
                .filter((article) => article.id !== campaign.id)
                .slice(0, 4)
                .map((article) => (
                  <Link
                    key={article.id}
                    href={`/khuyen-mai/${getArticleSlug(article)}`}
                    className="group grid grid-cols-[96px_1fr] gap-3 py-3"
                  >
                    <SafeImage
                      src={article.src}
                      alt={article.name}
                      className="aspect-[4/3] w-full rounded-md object-cover"
                      fallbackLabel="Tin khuyến mãi"
                    />
                    <h3 className="line-clamp-3 text-sm font-semibold leading-5 text-slate-800 group-hover:text-brand-blue">
                      {article.name}
                    </h3>
                  </Link>
                ))}
            </div>
          </aside>
        </div>
      </main>
    </AppShell>
  );
}
