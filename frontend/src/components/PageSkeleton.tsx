function Block({ className }: { className: string }) {
  return <div className={`animate-pulse rounded-xl bg-slate-200/80 ${className}`} />;
}

export function PageSkeleton() {
  return (
    <div className="min-h-screen bg-background">
      <Block className="h-[55px] w-full rounded-none" />
      <Block className="h-[72px] w-full rounded-none" />
      <div className="mx-auto max-w-[1200px] px-3 py-6 md:px-4">
        <Block className="h-5 w-56" />
        <Block className="mt-5 h-9 w-2/3 max-w-xl" />
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <Block className="h-[360px] w-full" />
          <Block className="h-[360px] w-full" />
        </div>
        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, index) => (
            <Block key={index} className="h-[300px] w-full" />
          ))}
        </div>
      </div>
    </div>
  );
}
