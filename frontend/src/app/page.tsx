import { AppShell } from "@/components/AppShell";
import { CategoryGrid } from "@/components/CategoryGrid";
import { FlashSale } from "@/components/FlashSale";
import { HeroCarousel } from "@/components/HeroCarousel";
import { ProductSections } from "@/components/ProductSections";
import { Topics } from "@/components/Topics";
import { fetchHomePageData } from "@/lib/home-data";

export default async function HomePage() {
  const data = await fetchHomePageData();

  return (
    <AppShell>
      <main className="min-h-full bg-background pb-2">
        <HeroCarousel
          slides={data.heroSlides}
          utilityBanners={data.utilityBanners}
        />
        <CategoryGrid categories={data.categories} />
        <FlashSale tabs={data.flashTabs} products={data.flashProducts} />
        <ProductSections
          tabs={data.featuredTabs}
          products={data.featuredProducts}
          banners={data.weeklyBanners}
        />
        <Topics articles={data.articles} searchTags={data.searchTags} />
      </main>
    </AppShell>
  );
}
