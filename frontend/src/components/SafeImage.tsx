"use client";

/* eslint-disable @next/next/no-img-element */
import { ImageOff } from "lucide-react";
import { useState, type ImgHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface SafeImageProps extends ImgHTMLAttributes<HTMLImageElement> {
  fallbackLabel?: string;
}

export function SafeImage({
  alt,
  className,
  fallbackLabel = "Điện máy XANH",
  onError,
  ...props
}: SafeImageProps) {
  const [hasError, setHasError] = useState(false);

  if (hasError || !props.src) {
    return (
      <div
        role="img"
        aria-label={alt || fallbackLabel}
        className={cn(
          "flex min-h-12 items-center justify-center gap-2 bg-[linear-gradient(135deg,#eff6ff,#f8fafc)] text-center text-xs font-semibold text-slate-400",
          className,
        )}
      >
        <ImageOff className="size-5 shrink-0" aria-hidden="true" />
        <span className="max-w-32 leading-4">{fallbackLabel}</span>
      </div>
    );
  }

  return (
    <img
      {...props}
      alt={alt || ""}
      className={className}
      onError={(event) => {
        setHasError(true);
        onError?.(event);
      }}
    />
  );
}
