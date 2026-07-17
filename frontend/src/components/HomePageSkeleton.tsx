function SkeletonBlock({ className }: { className: string }) {
  return <div className={`animate-pulse rounded-2xl bg-slate-200/80 ${className}`} />;
}

export function HomePageSkeleton() {
  return (
    <div className="min-h-screen bg-background">
      <SkeletonBlock className="h-14 w-full rounded-none" />
      <div className="mx-auto max-w-[1200px] px-3 py-4 md:px-4">
        <SkeletonBlock className="h-[220px] w-full md:h-[360px]" />
        <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-8">
          {Array.from({ length: 8 }).map((_, index) => (
            <SkeletonBlock key={index} className="h-[112px] w-full" />
          ))}
        </div>
        <SkeletonBlock className="mt-4 h-[420px] w-full" />
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <SkeletonBlock key={index} className="h-[180px] w-full" />
          ))}
        </div>
      </div>
    </div>
  );
}
