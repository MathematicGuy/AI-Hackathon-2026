import { homePageData } from "@/lib/home-data";
import type {
  CategoryItem,
  HeroSlide,
  ProductItem,
  PromoBanner,
} from "@/types/home";

const supplementalProducts: ProductItem[] = [
  {
    id: "catalog-air-fryer-magic-eco-ac-125",
    name: "Nồi chiên không dầu Magic Eco 6 lít AC-125",
    sub: "1700W - 6 lít",
    price: 1050000,
    originalPrice: 1990000,
    discount: "-47%",
    extra: "Online giá rẻ quá",
    rating: 5,
    soldLabel: "Đã bán 342",
    src: "https://cdnv2.tgdd.vn/mwg-static/dmx/Products/Images/9418/359867/noi-chien-khong-dau-magic-eco-6-lit-ac-125-1-639014752028717378.jpg",
    href: "https://www.dienmayxanh.com/noi-chien-khong-dau/noi-chien-khong-dau-magic-eco-6-lit-ac-125",
    category: "gia-dung",
    description: "Nồi chiên dung tích lớn, công nghệ Rapid Air và 8 chương trình nấu cài sẵn.",
    highlights: ["Dung tích 6 lít", "Công suất 1700W", "Điều khiển cảm ứng"],
    ctaLabel: "Xem ưu đãi",
  },
  {
    id: "catalog-dryer-electrolux-edv904h3wc",
    name: "Máy sấy thông hơi Electrolux 9 Kg EDV904H3WC",
    sub: "Úp ngược đặt lên máy giặt",
    price: 10490000,
    originalPrice: 10790000,
    discount: "-2%",
    extra: "Trả chậm 0% trả trước 0đ",
    rating: 4.9,
    soldLabel: "Đã bán 9,6k",
    src: "https://cdnv2.tgdd.vn/mwg-static/dmx/Products/Images/2202/329628/may-say-thong-hoi-electrolux-ultimatecare-9-kg-edv904h3wc-1-638733245772478815-700x467-638998332469937781.jpg",
    href: "https://www.dienmayxanh.com/may-say-quan-ao/may-say-thong-hoi-electrolux-ultimatecare-9-kg-edv904h3wc",
    category: "may-say-quan-ao",
    description: "Máy sấy thông hơi 9 kg phù hợp gia đình 3-5 người, có thể úp ngược để tiết kiệm diện tích.",
    highlights: ["Khối lượng sấy 9 kg", "Công nghệ sấy thông hơi", "Úp ngược linh hoạt"],
    ctaLabel: "Chọn gói dịch vụ",
  },
  {
    id: "catalog-freezer-sanaky-td-vh160vd",
    name: "Tủ đông Sanaky 118 lít TD.VH160VD",
    sub: "Tủ đông mini 1 cửa",
    price: 5590000,
    originalPrice: 7160000,
    discount: "-21%",
    extra: "Online giá rẻ quá",
    rating: 4.9,
    soldLabel: "Đã bán 390",
    src: "https://cdn.tgdd.vn/Products/Images/166/283526/tu-dong-sanaky-118lit-td.vh160vd-1-1.jpg",
    href: "https://www.dienmayxanh.com/tu-dong/tu-dong-sanaky-118-lit-tdvh160vd",
    category: "tu-dong",
    description: "Tủ đông đứng nhỏ gọn với 4 ngăn chứa, phù hợp gia đình cần trữ thực phẩm riêng biệt.",
    highlights: ["Dung tích 118 lít", "4 ngăn chứa", "Dàn lạnh hợp kim thép mạ đồng"],
    ctaLabel: "Xem chính sách giao hàng",
  },
  {
    id: "catalog-robot-xiaomi-vacuum-e5",
    name: "Robot hút bụi lau nhà Xiaomi Vacuum E5 - Trắng",
    sub: "Sạc 4.5 - 5.5 giờ, dùng 120 phút",
    price: 1990000,
    originalPrice: 2460000,
    discount: "-19%",
    extra: "Online giá rẻ quá",
    rating: 4.9,
    soldLabel: "Đã bán 958",
    src: "https://cdn.tgdd.vn/Products/Images/10139/327830/robot-hut-bui-lau-nha-xiaomi-vacuum-e5-trang-fix-1.jpg",
    href: "https://www.dienmayxanh.com/robot-hut-bui/robot-hut-bui-lau-nha-xiaomi-vacuum-e5-trang",
    category: "robot-hut-bui",
    description: "Robot vừa hút vừa lau, điều khiển qua Mi Home và tự quay về đế sạc.",
    highlights: ["Dùng khoảng 120 phút", "Hộp bụi 400 ml", "Điều khiển qua điện thoại"],
    ctaLabel: "Xem tính năng",
  },
  {
    id: "catalog-fan-senko-dh1600",
    name: "Quạt đứng Senko 3 cánh DH1600 47W",
    sub: "3 mức gió - điều chỉnh chiều cao",
    price: 550000,
    originalPrice: 700000,
    discount: "-21%",
    extra: "Thứ 4 sale sập sàn",
    rating: 4.9,
    soldLabel: "Đã bán 92,5k",
    src: "https://cdn.tgdd.vn/Products/Images/1992/268450/dung-senko-dh1600-3.jpg",
    href: "https://www.dienmayxanh.com/quat/dung-senko-dh1600",
    category: "quat",
    description: "Quạt đứng động cơ bạc thau, 3 tốc độ gió và hẹn giờ tắt tiện dụng.",
    highlights: ["Công suất 47W", "3 cánh - 39 cm", "Điều chỉnh chiều cao"],
    ctaLabel: "Xem màu sản phẩm",
  },
  {
    id: "catalog-rice-cooker-sharp-ks-com191ev-wh",
    name: "Nồi cơm điện tử Sharp 1.8 lít KS-COM191EV-WH",
    sub: "Dung tích 1.8 lít",
    price: 1690000,
    originalPrice: 1860000,
    discount: "-9%",
    extra: "Giảm giá online",
    rating: 4.9,
    soldLabel: "Đã bán 12,8k",
    src: "https://cdn.tgdd.vn/Products/Images/1922/311381/noi-com-dien-tu-sharp-18-lit-ks-com191ev-wh-1.jpg",
    href: "https://www.dienmayxanh.com/noi-com-dien/noi-com-dien-tu-sharp-18-lit-ks-com191ev-wh",
    category: "noi-com-dien",
    description: "Nồi cơm điện tử dung tích 1.8 lít với nhiều chế độ nấu cho gia đình 4-6 người.",
    highlights: ["Dung tích 1.8 lít", "Nhiều chế độ nấu", "Hẹn giờ tiện lợi"],
    ctaLabel: "Xem chương trình nấu",
  },
];

export const allProducts = [
  ...homePageData.flashProducts,
  ...homePageData.featuredProducts,
  ...supplementalProducts,
].filter(
  (product, index, products) =>
    products.findIndex((candidate) => candidate.id === product.id) === index,
);

export function slugFromHref(href: string) {
  try {
    const url = new URL(href, "https://www.dienmayxanh.com");
    return url.pathname.split("/").filter(Boolean).at(-1) || "trang-chu";
  } catch {
    return href.replace(/^\/+|\/+$/g, "") || "trang-chu";
  }
}

export function getCategorySlug(category: CategoryItem) {
  return slugFromHref(category.href);
}

export function getProductSlug(product: ProductItem) {
  return slugFromHref(product.href);
}

export function getProductCategorySlug(product: ProductItem) {
  const explicitCategory = homePageData.categories.some(
    (category) => getCategorySlug(category) === product.category,
  );
  if (explicitCategory) {
    return product.category;
  }

  try {
    const url = new URL(product.href, "https://www.dienmayxanh.com");
    return url.pathname.split("/").filter(Boolean)[0] || "danh-muc";
  } catch {
    return "danh-muc";
  }
}

export function getArticleSlug(article: ProductItem) {
  return slugFromHref(article.href);
}

export function getCampaignSlug(item: HeroSlide | PromoBanner) {
  return slugFromHref(item.href);
}

export function getCategoryBySlug(slug: string) {
  return homePageData.categories.find(
    (category) => category.id === slug || getCategorySlug(category) === slug,
  );
}

export function getProductBySlug(slug: string) {
  return allProducts.find(
    (product) => product.id === slug || getProductSlug(product) === slug,
  );
}

export function getArticleBySlug(slug: string) {
  return homePageData.articles.find(
    (article) => article.id === slug || getArticleSlug(article) === slug,
  );
}

export function getCampaignBySlug(slug: string) {
  const article = getArticleBySlug(slug);
  if (article) {
    return {
      id: article.id,
      title: article.name,
      description: article.description || article.sub,
      src: article.src,
      publishedAt: article.publishedAt,
      kind: "article" as const,
    };
  }

  const banner = homePageData.weeklyBanners.find(
    (item) => item.id === slug || getCampaignSlug(item) === slug,
  );
  if (banner) {
    return {
      id: banner.id,
      title: banner.title,
      description: banner.description || "Chương trình ưu đãi nổi bật.",
      src: banner.src,
      kind: "campaign" as const,
    };
  }

  const hero = homePageData.heroSlides.find(
    (item) => item.id === slug || getCampaignSlug(item) === slug,
  );
  if (hero) {
    return {
      id: hero.id,
      title: hero.title || hero.alt,
      description: hero.description || "Chương trình ưu đãi nổi bật.",
      src: hero.src,
      kind: "campaign" as const,
    };
  }

  return undefined;
}

const categoryAliases: Record<string, string[]> = {
  "may-lanh": ["may-lanh", "cooling"],
  "tu-lanh": ["tu-lanh", "refrigerator"],
  tivi: ["tivi", "tv"],
  "may-giat": ["may-giat", "laundry"],
  "quat-dieu-hoa": ["quat-dieu-hoa"],
  "gia-dung": ["gia-dung", "noi-chien-khong-dau"],
  "may-loc-nuoc": ["may-loc-nuoc"],
  "may-say-quan-ao": ["may-say-quan-ao"],
  "tu-dong": ["tu-dong"],
  "robot-hut-bui": ["robot-hut-bui"],
  quat: ["quat"],
  "noi-com-dien": ["noi-com-dien"],
};

export function getProductsForCategory(slug: string) {
  const aliases = categoryAliases[slug] || [slug];
  const matched = allProducts.filter((product) => {
    const routeCategory = getProductCategorySlug(product);
    return aliases.includes(product.category) || aliases.includes(routeCategory);
  });

  return matched;
}

function normalize(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .replace(/[^a-zA-Z0-9]+/g, " ")
    .trim()
    .replace(/\s+/g, " ")
    .toLocaleLowerCase("vi-VN");
}

export function searchProducts(query: string) {
  const normalized = normalize(query.trim());
  if (!normalized) {
    return [];
  }

  return allProducts.filter((product) => {
    const routeCategory = getProductCategorySlug(product);
    const haystack = normalize(
      `${product.name} ${product.sub} ${product.category} ${routeCategory}`,
    );
    return haystack.includes(normalized);
  });
}
