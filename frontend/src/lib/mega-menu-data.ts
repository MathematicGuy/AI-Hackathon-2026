export interface MegaMenuItem {
  id: string;
  label: string;
  href: string;
  image: string;
  badge?: "Hot" | "Mới";
}

export interface MegaMenuSection {
  id: string;
  title: string;
  items: MegaMenuItem[];
}

export interface MegaMenuNavigationItem {
  id: string;
  label: string;
}

export const megaMenuNavigation: MegaMenuNavigationItem[] = [
  { id: "hot", label: "Chương trình hot" },
  { id: "standard", label: "Hàng chuẩn, giá mê" },
  { id: "electronics", label: "Điện tử, điện lạnh" },
  { id: "electric-appliances", label: "Điện gia dụng" },
  { id: "home-appliances", label: "Đồ gia dụng" },
  { id: "technology", label: "Điện thoại, laptop, công nghệ" },
  { id: "accessories", label: "Phụ kiện" },
  { id: "beauty", label: "Làm đẹp, chăm sóc cá nhân" },
  { id: "used", label: "Máy cũ, trưng bày" },
  { id: "other", label: "Sản phẩm khác" },
  { id: "services", label: "Thông tin - Dịch vụ tiện ích" },
];

export const hotMenuSections: MegaMenuSection[] = [
  {
    id: "hot-campaigns",
    title: "CHƯƠNG TRÌNH HOT",
    items: [
      { id: "flashsale", label: "Flash sale giảm đến 50%", href: "/flashsale", image: "/images/menu/hot-flash-sale.png" },
      { id: "online-only", label: "Gia dụng Online - Săn quà 0đ mỗi ngày", href: "/danh-muc/gia-dung", image: "/images/menu/hot-online-only.png" },
      { id: "cool-station", label: "Trạm dừng mát lạnh, săn deal 0đ", href: "/danh-muc/may-lanh", image: "/images/menu/hot-cool-station.png" },
      { id: "blender", label: "Xay ép tiện lợi", href: "/tim-kiem?q=máy%20xay", image: "/images/menu/hot-blender.png" },
      { id: "water-filter", label: "Máy lọc nước RO giá chỉ từ 4.150k", href: "/danh-muc/may-loc-nuoc", image: "/images/menu/hot-water-filter.png" },
      { id: "aqua-haier", label: "Tuần lễ thương hiệu Máy giặt Aqua Haier", href: "/danh-muc/may-giat", image: "/images/menu/hot-aqua-haier.png" },
      { id: "clearance", label: "Xả kho giá sốc", href: "/khuyen-mai", image: "/images/menu/hot-clearance.png" },
      { id: "water-dispenser", label: "Cây nóng lạnh giảm giá đến 45%", href: "/tim-kiem?q=cây%20nóng%20lạnh", image: "/images/menu/hot-water-dispenser.png" },
      { id: "hand-tools", label: "Dụng Cụ Cầm Tay Giảm 50%", href: "/tim-kiem?q=dụng%20cụ", image: "/images/menu/hot-hand-tools.png" },
      { id: "stove", label: "Mua bếp điện, trợ giá đến 1 triệu", href: "/tim-kiem?q=bếp%20điện", image: "/images/menu/hot-stove.png" },
      { id: "rice-cooker", label: "Mua nồi cơm tặng bàn ủi", href: "/danh-muc/noi-com-dien", image: "/images/menu/hot-rice-cooker.png" },
      { id: "fridge", label: "Mua tủ lạnh tặng quà (tùy model)", href: "/danh-muc/tu-lanh", image: "/images/menu/hot-fridge.png" },
      { id: "large-tv", label: "Mua tivi >55\" tặng quà (tuỳ model)", href: "/danh-muc/tivi", image: "/images/menu/hot-large-tv.png" },
      { id: "health-beauty", label: "Chăm sóc sức khỏe - làm đẹp", href: "/tim-kiem?q=chăm%20sóc", image: "/images/menu/hot-health-beauty.png" },
      { id: "kitchen", label: "Nhà bếp giảm đến 50%", href: "/danh-muc/gia-dung", image: "/images/menu/hot-kitchen.png" },
      { id: "installation", label: "Gia dụng lắp đặt giảm đến 50%", href: "/danh-muc/gia-dung", image: "/images/menu/hot-installation.png" },
      { id: "dehumidifier", label: "100% Máy hút ẩm tặng quà", href: "/tim-kiem?q=máy%20hút%20ẩm", image: "/images/menu/hot-dehumidifier.png" },
      { id: "premium", label: "Hàng cao cấp giảm đến 50%", href: "/khuyen-mai", image: "/images/menu/hot-premium.png" },
      { id: "camera", label: "Camera giám sát giá chỉ từ 450.000đ", href: "/tim-kiem?q=camera", image: "/images/menu/hot-camera.jpg", badge: "Hot" },
      { id: "solar-light", label: "Đèn năng lượng mặt trời từ 110K", href: "/tim-kiem?q=đèn%20năng%20lượng", image: "/images/menu/hot-solar-light.png", badge: "Mới" },
    ],
  },
];

export const serviceMenuSections: MegaMenuSection[] = [
  {
    id: "information",
    title: "THÔNG TIN",
    items: [
      { id: "buying-advice", label: "Tư vấn chọn mua", href: "/tien-ich/tu-van-chon-mua", image: "/images/menu/info-buying-advice.png" },
      { id: "promotions", label: "Khuyến mãi", href: "/khuyen-mai", image: "/images/menu/info-promotions.png" },
      { id: "stores", label: "Tìm địa chỉ cửa hàng", href: "/tien-ich/tim-cua-hang", image: "/images/menu/info-stores.png" },
      { id: "installments", label: "Tìm hiểu về mua trả chậm", href: "/tien-ich/mua-tra-cham", image: "/images/menu/info-installments.png" },
      { id: "warranty", label: "Tra cứu bảo hành", href: "/tien-ich/tra-cuu-bao-hanh", image: "/images/menu/info-warranty.png" },
    ],
  },
  {
    id: "utilities",
    title: "DỊCH VỤ TIỆN ÍCH",
    items: [
      { id: "clean-ac", label: "Vệ sinh máy lạnh", href: "/tien-ich/ve-sinh-may-lanh", image: "/images/menu/service-clean-ac.png" },
      { id: "replace-filter", label: "Thay lõi lọc nước", href: "/tien-ich/thay-loi-loc-nuoc", image: "/images/menu/service-replace-filter.png" },
      { id: "clean-washer", label: "Vệ sinh máy giặt", href: "/tien-ich/ve-sinh-may-giat", image: "/images/menu/service-clean-washer.png" },
      { id: "vehicle-insurance", label: "Bảo hiểm Ô tô - Xe máy", href: "/tien-ich/bao-hiem-xe", image: "/images/menu/service-vehicle-insurance.png" },
      { id: "sim-card", label: "Sim số, thẻ cào", href: "/tien-ich/sim-the-cao", image: "/images/menu/service-sim-card.png" },
      { id: "pay-installment", label: "Đóng tiền trả góp", href: "/tien-ich/dong-tien-tra-gop", image: "/images/menu/service-pay-installment.png" },
      { id: "online-grocery", label: "Đi chợ online", href: "/tien-ich/di-cho-online", image: "/images/menu/service-online-grocery.png" },
      { id: "cake", label: "Vay tiền mặt CAKE", href: "/tien-ich/vay-cake", image: "/images/menu/service-cake.png" },
      { id: "cathay", label: "Vay tiền mặt CATHAY", href: "/tien-ich/vay-cathay", image: "/images/menu/service-cathay.png" },
      { id: "flight", label: "Đặt vé máy bay", href: "/tien-ich/dat-ve-may-bay", image: "/images/menu/service-flight.png" },
      { id: "kredivo", label: "Vay tiền mặt KREDIVO", href: "/tien-ich/vay-kredivo", image: "/images/menu/service-kredivo.png" },
      { id: "evomoney", label: "Vay tiền mặt Evomoney", href: "/tien-ich/vay-evomoney", image: "/images/menu/service-evomoney.png" },
    ],
  },
];

export const serviceMenuItems = serviceMenuSections.flatMap((section) => section.items);

export function getServiceMenuItem(slug: string) {
  return serviceMenuItems.find((item) => item.href.endsWith(`/${slug}`));
}
