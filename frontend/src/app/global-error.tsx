"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string };
  unstable_retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <html lang="vi" suppressHydrationWarning>
      <body className="min-h-screen bg-[#f2f4f7] font-sans" suppressHydrationWarning>
        <main className="mx-auto flex min-h-screen max-w-3xl items-center px-4 py-16">
          <div className="w-full rounded-3xl border border-rose-200 bg-white px-6 py-10 text-center shadow-sm">
            <title>Điện máy XANH</title>
            <h1 className="text-2xl font-bold text-slate-900">Ứng dụng tạm thời bị gián đoạn</h1>
            <p className="mt-3 text-sm leading-6 text-slate-500">
              Đã có lỗi ngoài dự kiến ở lớp layout gốc. Bạn có thể thử tải lại để khôi phục phiên hiện tại.
            </p>
            <button
              onClick={() => unstable_retry()}
              className="mt-6 inline-flex h-11 items-center justify-center rounded-full bg-[#288ad6] px-5 text-sm font-semibold text-white transition hover:bg-sky-600 active:bg-sky-700"
            >
              Tải lại ứng dụng
            </button>
          </div>
        </main>
      </body>
    </html>
  );
}
