import Link from "next/link";
import { SafeImage } from "@/components/SafeImage";
import { StateCard } from "@/components/StateCard";
import { getArticleSlug } from "@/lib/catalog";
import { formatDate } from "@/lib/format";
import type { ProductItem, SearchTag } from "@/types/home";

interface TopicsProps {
  articles: ProductItem[];
  searchTags: SearchTag[];
}

export function Topics({ articles, searchTags }: TopicsProps) {
  return (
    <section className="mx-auto max-w-[1200px] px-3 py-4 md:px-4">
      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-bold text-slate-900">#CHỦ ĐỀ</h2>
            <Link
              href="/khuyen-mai"
              className="text-sm font-semibold text-brand-blue transition hover:underline active:opacity-70"
            >
              Xem thêm
            </Link>
          </div>

          {articles.length ? (
            <div className="grid gap-3 md:grid-cols-2">
              {articles.map((article) => (
                <Link
                  key={article.id}
                  href={`/khuyen-mai/${getArticleSlug(article)}`}
                  className="group overflow-hidden rounded-xl border border-slate-100 text-left transition hover:-translate-y-0.5 hover:shadow-md active:translate-y-0"
                >
                  <SafeImage
                    src={article.src}
                    alt={article.name}
                    className="aspect-[16/9] w-full object-cover transition group-hover:scale-[1.02]"
                    fallbackLabel={article.name}
                    loading="lazy"
                  />
                  <div className="p-3">
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <p className="text-xs font-bold uppercase tracking-wide text-brand-blue">
                        {article.sub}
                      </p>
                      {article.publishedAt ? (
                        <time
                          dateTime={article.publishedAt}
                          className="text-xs text-slate-400"
                        >
                          {formatDate(article.publishedAt)}
                        </time>
                      ) : null}
                    </div>
                    <h3 className="line-clamp-2 text-sm font-semibold leading-5 text-slate-800 group-hover:text-brand-blue">
                      {article.name}
                    </h3>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <StateCard
              title="Chưa có bài viết nổi bật"
              description="Hiện chưa có nội dung chủ đề để hiển thị."
            />
          )}
        </div>

        <div className="rounded-xl bg-white p-4 shadow-sm">
          <h2 className="mb-4 text-xl font-bold text-slate-900">
            Mọi người cũng tìm kiếm
          </h2>
          {searchTags.length ? (
            <div className="flex flex-wrap gap-2">
              {searchTags.map((tag) => (
                <Link
                  key={tag.id}
                  href={`/tim-kiem?q=${encodeURIComponent(tag.label)}`}
                  className="rounded-full bg-slate-100 px-3 py-2 text-sm text-slate-700 transition hover:bg-slate-200 hover:text-brand-blue active:translate-y-px"
                >
                  {tag.label}
                </Link>
              ))}
            </div>
          ) : (
            <StateCard
              title="Chưa có từ khóa gợi ý"
              description="Danh sách tìm kiếm phổ biến sẽ xuất hiện ở đây khi dữ liệu sẵn sàng."
            />
          )}
        </div>
      </div>
    </section>
  );
}
