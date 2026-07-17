"use client";

import { useEffect } from "react";
import { StateCard } from "@/components/StateCard";

export default function Error({
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
    <main className="min-h-screen bg-background px-4 py-16">
      <div className="mx-auto max-w-3xl">
        <StateCard
          title="Trang đang gặp sự cố"
          description="Rất tiếc, dữ liệu trang này chưa thể hiển thị. Vui lòng thử tải lại để tiếp tục."
          actionLabel="Thử lại"
          onAction={unstable_retry}
        />
      </div>
    </main>
  );
}
