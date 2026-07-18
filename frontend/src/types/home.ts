export interface HeroSlide {
  id: string;
  href: string;
  src: string;
  alt: string;
  title?: string;
  description?: string;
}

export interface UtilityBanner {
  id: string;
  label: string;
}

export interface CategoryItem {
  id: string;
  href: string;
  badge?: string;
  name: string;
  src: string;
  description?: string;
}

export interface FlashTab {
  id: string;
  label: string;
  src?: string;
}

export interface ProductItem {
  id: string;
  name: string;
  sub: string;
  price: number;
  originalPrice?: number;
  discount?: string;
  extra?: string;
  rating?: number;
  soldLabel?: string;
  remain?: string;
  src: string;
  href: string;
  category: string;
  publishedAt?: string;
  description?: string;
  highlights?: string[];
  ctaLabel?: string;
}

export interface PromoBanner {
  id: string;
  title: string;
  src: string;
  href: string;
  description?: string;
}

export interface SearchTag {
  id: string;
  label: string;
}

export interface SupportContact {
  label: string;
  value: string;
  note: string;
}

export interface HomePageData {
  appName: string;
  heroSlides: HeroSlide[];
  utilityBanners: UtilityBanner[];
  categories: CategoryItem[];
  flashTabs: FlashTab[];
  flashProducts: ProductItem[];
  featuredTabs: FlashTab[];
  featuredProducts: ProductItem[];
  weeklyBanners: PromoBanner[];
  articles: ProductItem[];
  searchTags: SearchTag[];
  supportContacts: SupportContact[];
}
