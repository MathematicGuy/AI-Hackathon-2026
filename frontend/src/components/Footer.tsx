import Link from "next/link";
import type { SupportContact } from "@/types/home";
import {
  BachHoaXanhLogo,
  DienMayXanhLogo,
  TheGioiDiDongLogo,
  TopZoneLogo,
} from "./icons";

const companyLinks = [
  { label: "Giới thiệu công ty (DMX.vn)", href: "/khuyen-mai" },
  { label: "Tuyển dụng", href: "/khuyen-mai" },
  { label: "Gửi góp ý, khiếu nại", href: "/dang-nhap" },
  { label: "Tìm siêu thị (2989 shop)", href: "/danh-muc" },
];

const otherLinks = [
  { label: "Tích điểm Quà tặng VIP", href: "/dang-nhap" },
  { label: "Lịch sử mua hàng", href: "/dang-nhap" },
  { label: "Đăng ký bán hàng CTV chiết khấu cao", href: "/dang-nhap" },
  { label: "Tìm hiểu về mua trả chậm", href: "/khuyen-mai" },
];

interface FooterProps {
  supportContacts: SupportContact[];
}

export function Footer({ supportContacts }: FooterProps) {
  return (
    <footer className="mt-auto border-t border-slate-200 bg-white">
      <div className="mx-auto max-w-[1200px] px-3 py-7 md:px-4">
        <div className="grid gap-6 border-b border-slate-200 pb-6 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <h2 className="mb-3 text-base font-bold text-slate-900">Tổng đài hỗ trợ</h2>
            <div className="space-y-2 text-sm text-slate-700">
              {supportContacts.map((item) => (
                <p key={item.label}>
                  {item.label}: {" "}
                  <a
                    href={`tel:${item.value.replace(/\D/g, "")}`}
                    className="font-bold text-brand-blue hover:underline"
                  >
                    {item.value}
                  </a>{" "}
                  ({item.note})
                </p>
              ))}
            </div>
          </div>

          <div>
            <h2 className="mb-3 text-base font-bold text-slate-900">Về công ty</h2>
            <div className="space-y-2 text-sm text-slate-700">
              {companyLinks.map((item) => (
                <p key={item.label}>
                  <Link href={item.href} className="hover:text-brand-blue hover:underline">
                    {item.label}
                  </Link>
                </p>
              ))}
            </div>
          </div>

          <div>
            <h2 className="mb-3 text-base font-bold text-slate-900">Thông tin khác</h2>
            <div className="space-y-2 text-sm text-slate-700">
              {otherLinks.map((item) => (
                <p key={item.label}>
                  <Link href={item.href} className="hover:text-brand-blue hover:underline">
                    {item.label}
                  </Link>
                </p>
              ))}
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4 border-b border-slate-200 py-5">
          <span className="text-sm font-semibold text-slate-700">Website cùng tập đoàn</span>
          <DienMayXanhLogo className="h-8" />
          <TheGioiDiDongLogo />
          <TopZoneLogo />
          <BachHoaXanhLogo />
        </div>

        <div className="space-y-2 pt-5 text-[11px] leading-5 text-slate-500">
          <p>
            © 2018. Công Ty Cổ Phần Đầu Tư Điện Máy Xanh. GPDKKD: 0303217354 do sở
            KH &amp; ĐT TP.HCM cấp ngày 02/01/2007. GPMXH: 21/GP-BTTTT do Bộ
            Thông Tin và Truyền Thông cấp ngày 11/01/2021.
          </p>
          <p>
            Địa chỉ: 128 Trần Quang Khải, P.Tân Định, TP. Hồ Chí Minh. Điện thoại:
            028 38125960. Email: hotrotmdt@thegioididong.com.
          </p>
        </div>
      </div>
    </footer>
  );
}
