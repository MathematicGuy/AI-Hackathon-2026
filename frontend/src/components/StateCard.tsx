"use client";

import { Button } from "@/components/ui/button";

interface StateCardProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function StateCard({
  title,
  description,
  actionLabel,
  onAction,
}: StateCardProps) {
  return (
    <div className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-10 text-center shadow-sm">
      <h2 className="text-lg font-bold text-slate-900">{title}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-500">
        {description}
      </p>
      {actionLabel && onAction ? (
        <div className="mt-5">
          <Button
            onClick={onAction}
            className="h-10 rounded-full bg-brand-blue px-5 text-white hover:bg-sky-600 active:bg-sky-700 disabled:bg-slate-300"
          >
            {actionLabel}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
