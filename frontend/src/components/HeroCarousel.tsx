"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { SafeImage } from "@/components/SafeImage";
import { getCampaignSlug } from "@/lib/catalog";
import type { HeroSlide, UtilityBanner } from "@/types/home";

interface HeroCarouselProps {
  slides: HeroSlide[];
  utilityBanners: UtilityBanner[];
}

export function HeroCarousel({ slides, utilityBanners }: HeroCarouselProps) {
  const [activeSlide, setActiveSlide] = useState(0);

  useEffect(() => {
    if (slides.length <= 1) {
      return;
    }

    const timer = window.setInterval(() => {
      setActiveSlide((value) => (value + 1) % slides.length);
    }, 4000);

    return () => window.clearInterval(timer);
  }, [slides.length]);

  return (
    <section className="mx-auto max-w-[1200px] px-3 pt-3 md:px-4 md:pt-4">
      <div className="overflow-hidden rounded-xl bg-white shadow-sm">
        <div className="relative aspect-[16/8] overflow-hidden md:aspect-[16/5]">
          {slides.map((slide, index) => (
            <Link
              key={slide.id}
              href={`/khuyen-mai/${getCampaignSlug(slide)}`}
              className={`absolute inset-0 transition-opacity duration-500 ${
                index === activeSlide
                  ? "opacity-100"
                  : "pointer-events-none opacity-0"
              }`}
              aria-hidden={index !== activeSlide}
            >
              <SafeImage
                src={slide.src}
                alt={slide.alt}
                className="h-full w-full object-cover"
                loading={index === 0 ? "eager" : "lazy"}
                fallbackLabel={slide.title || slide.alt}
              />
            </Link>
          ))}

          <div className="absolute bottom-3 left-1/2 flex -translate-x-1/2 gap-2">
            {slides.map((slide, index) => (
              <button
                key={slide.id}
                type="button"
                onClick={() => setActiveSlide(index)}
                className={`h-2.5 rounded-full transition-all hover:bg-white active:scale-90 ${
                  activeSlide === index ? "w-6 bg-white" : "w-2.5 bg-white/60"
                }`}
                aria-label={`Hiển thị banner ${index + 1}`}
                aria-current={activeSlide === index}
              />
            ))}
          </div>
        </div>

        <div className="grid gap-2 p-3 md:grid-cols-2 md:p-4">
          {utilityBanners.map((item) => (
            <Link
              key={item.id}
              href={`/tim-kiem?q=${encodeURIComponent(item.label)}`}
              className="rounded-full bg-[#f4f8ff] px-4 py-2 text-sm font-semibold text-brand-blue transition hover:bg-[#e6f1ff] active:translate-y-px"
            >
              {item.label}
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
