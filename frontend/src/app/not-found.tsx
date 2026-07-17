import Link from "next/link";
import { SearchX } from "lucide-react";
import { AppShell } from "@/components/AppShell";

export default function NotFound() {
  return (
    <AppShell>
      <main className="mx-auto flex min-h-[560px] max-w-[720px] flex-col items-center justify-center px-4 py-12 text-center">
        <SearchX className="size-20 text-slate-300" />
        <p className="mt-5 text-sm font-bold text-brand-blue">LỖI 404</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-900">Không tìm thấy trang</h1>
        <p className="mt-3 max-w-lg text-sm leading-6 text-slate-500">
          Đường dẫn không tồn tại trong dữ liệu clone hoặc nội dung đã được chuyển sang trang khác.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link href="/" className="rounded-lg bg-brand-blue px-5 py-3 text-sm font-bold text-white transition hover:bg-[#1978c4] active:translate-y-px">
            Về trang chủ
          </Link>
          <Link href="/danh-muc" className="rounded-lg border border-slate-200 bg-white px-5 py-3 text-sm font-bold text-slate-700 transition hover:border-sky-300 hover:bg-sky-50 active:translate-y-px">
            Xem danh mục
          </Link>
        </div>
      </main>
    </AppShell>
  );
}
