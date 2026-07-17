import type { Metadata } from "next";
import { CircleCheck, Settings, ShieldCheck, Truck } from "lucide-react";
import { notFound } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { ProductCard } from "@/components/ProductCard";
import { ProductDetailClient } from "@/components/ProductDetailClient";
import {
  allProducts,
  getCategoryBySlug,
  getProductBySlug,
  getProductCategorySlug,
  getProductSlug,
  getProductsForCategory,
} from "@/lib/catalog";

interface ProductPageProps {
  params: Promise<{ slug: string }>;
}

export function generateStaticParams() {
  return allProducts.map((product) => ({ slug: getProductSlug(product) }));
}

export async function generateMetadata({ params }: ProductPageProps): Promise<Metadata> {
  const { slug } = await params;
  const product = getProductBySlug(slug);
  return {
    title: product ? `${product.name} | Điện máy XANH` : "Sản phẩm | Điện máy XANH",
    description: product?.description,
  };
}

function getSpecifications(categorySlug: string) {
  if (categorySlug === "may-lanh") {
    return [
      ["Loại máy", "1 chiều (chỉ làm lạnh)"],
      ["Inverter", "Có Inverter"],
      ["Công suất làm lạnh", "1 HP - 9.500 BTU"],
      ["Phạm vi làm lạnh", "Dưới 15m²"],
      ["Độ ồn trung bình", "Dàn lạnh 36 dB - Dàn nóng 52 dB"],
      ["Dòng sản phẩm", "2026"],
      ["Sản xuất tại", "Thái Lan"],
      ["Bảo hành", "Chính hãng 3 năm"],
      ["Loại Gas", "R-32"],
    ];
  }

  return [
    ["Tình trạng", "Hàng mới, chính hãng"],
    ["Năm ra mắt", "2026"],
    ["Bảo hành", "Theo chính sách nhà sản xuất"],
    ["Giao hàng", "Tận nơi trên toàn quốc"],
    ["Đổi trả", "Hư gì đổi nấy theo điều kiện áp dụng"],
  ];
}

export default async function ProductPage({ params }: ProductPageProps) {
  const { slug } = await params;
  const product = getProductBySlug(slug);

  if (!product) {
    notFound();
  }

  const categorySlug = getProductCategorySlug(product);
  const category = getCategoryBySlug(categorySlug);
  const specifications = getSpecifications(categorySlug);
  const sameCategoryProducts = getProductsForCategory(categorySlug).filter(
    (item) => item.id !== product.id,
  );
  const fallbackProducts = allProducts.filter(
    (item) => item.id !== product.id && !sameCategoryProducts.some((related) => related.id === item.id),
  );
  const relatedProducts = [...sameCategoryProducts, ...fallbackProducts].slice(0, 5);

  return (
    <AppShell>
      <main className="mx-auto w-full max-w-[1200px] px-3 py-5 md:px-4">
        <Breadcrumbs
          items={[
            { label: "Trang chủ", href: "/" },
            category
              ? { label: category.name, href: `/danh-muc/${categorySlug}` }
              : { label: "Sản phẩm", href: "/danh-muc" },
            { label: product.name },
          ]}
        />

        <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-slate-200 pb-4">
          <h1 className="text-xl font-bold text-slate-950 md:text-2xl">{product.name}</h1>
          {product.soldLabel ? <span className="text-sm text-slate-400">{product.soldLabel}</span> : null}
          {product.rating ? (
            <span className="text-sm font-semibold text-amber-500">★ {product.rating.toFixed(1)}</span>
          ) : null}
          <span className="text-sm font-medium text-brand-blue">Thông số</span>
          <span className="text-sm font-medium text-brand-blue">So sánh</span>
        </div>

        <ProductDetailClient product={product} />

        <section className="mt-4 rounded-xl bg-white p-4 shadow-sm md:p-5">
          <h2 className="text-xl font-bold text-slate-900">Điện Máy XANH cam kết</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { icon: CircleCheck, text: "Hư gì đổi nấy 12 tháng tận nhà" },
              { icon: ShieldCheck, text: "Bảo hành chính hãng, hỗ trợ tận nơi" },
              { icon: Settings, text: "Lắp đặt đúng kỹ thuật" },
              { icon: Truck, text: "Giao hàng nhanh chóng tùy khu vực" },
            ].map((item) => (
              <div key={item.text} className="flex gap-3 rounded-lg bg-slate-50 p-3 text-sm leading-5 text-slate-700">
                <item.icon className="size-6 shrink-0 text-brand-blue" />
                <span>{item.text}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-4 rounded-xl bg-white p-4 shadow-sm md:p-5">
          <h2 className="text-xl font-bold text-slate-900">Thông số kỹ thuật</h2>
          <dl className="mt-4 overflow-hidden rounded-lg border border-slate-200">
            {specifications.map(([label, value], index) => (
              <div
                key={label}
                className={`grid grid-cols-[minmax(120px,35%)_1fr] gap-3 px-3 py-3 text-sm ${
                  index % 2 === 0 ? "bg-slate-50" : "bg-white"
                }`}
              >
                <dt className="text-slate-500">{label}</dt>
                <dd className="font-medium text-slate-800">{value}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section className="mt-4 rounded-xl bg-white p-3 shadow-sm md:p-4">
          <h2 className="px-1 text-xl font-bold text-slate-900">Sản phẩm thường mua cùng</h2>
          <div className="mt-4 grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-5">
            {relatedProducts.map((item) => (
              <ProductCard key={item.id} product={item} />
            ))}
          </div>
        </section>
      </main>
    </AppShell>
  );
}
