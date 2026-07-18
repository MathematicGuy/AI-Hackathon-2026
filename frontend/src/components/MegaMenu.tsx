"use client";

import { X } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { SafeImage } from "@/components/SafeImage";
import { getCategorySlug } from "@/lib/catalog";
import {
  hotMenuSections,
  megaMenuNavigation,
  serviceMenuSections,
  type MegaMenuItem,
  type MegaMenuSection,
} from "@/lib/mega-menu-data";
import type { CategoryItem } from "@/types/home";

interface MegaMenuProps {
  categories: CategoryItem[];
  isOpen: boolean;
  onClose: () => void;
}

const categoryIndexes: Record<string, number[]> = {
  standard: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
  electronics: [0, 1, 2, 3, 4, 7, 8],
  "electric-appliances": [5, 6, 11],
  "home-appliances": [2, 9, 10, 11],
  technology: [4, 9],
  accessories: [6, 9, 10],
  beauty: [5, 9],
  used: [0, 1, 3, 4],
  other: [6, 8, 10, 11],
};

function sectionsForPanel(activePanel: string, categories: CategoryItem[]): MegaMenuSection[] {
  if (activePanel === "hot") {
    return hotMenuSections;
  }
  if (activePanel === "services") {
    return serviceMenuSections;
  }

  const indexes = categoryIndexes[activePanel] || categoryIndexes.standard;
  const selected = indexes.map((index) => categories[index]).filter(Boolean);
  const navigationItem = megaMenuNavigation.find((item) => item.id === activePanel);

  return [
    {
      id: activePanel,
      title: navigationItem?.label.toLocaleUpperCase("vi-VN") || "DANH MỤC",
      items: selected.map((category) => ({
        id: category.id,
        label: category.name,
        href: `/danh-muc/${getCategorySlug(category)}`,
        image: category.src,
      })),
    },
  ];
}

function MenuItemCard({ item, onNavigate }: { item: MegaMenuItem; onNavigate: () => void }) {
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      className="group relative flex min-h-[99px] w-[70px] shrink-0 flex-col items-center rounded-lg px-0 py-[7px] text-center text-xs leading-4 text-[#333] transition hover:bg-[#f4f8ff] hover:text-[#0068d7] active:bg-[#eaf3ff]"
    >
      <span className="relative mb-[5px] flex size-12 items-center justify-center">
        <SafeImage
          src={item.image}
          alt={item.label}
          className="max-h-[90%] max-w-[90%] object-contain transition duration-200 group-hover:scale-105"
          fallbackLabel={item.label}
        />
        {item.badge ? (
          <span className="absolute -right-3 -top-2 rounded bg-rose-50 px-1 py-0.5 text-[10px] leading-3 text-rose-500">
            {item.badge}
          </span>
        ) : null}
      </span>
      <span className="line-clamp-3">{item.label}</span>
    </Link>
  );
}

function MenuContent({ sections, onNavigate }: { sections: MegaMenuSection[]; onNavigate: () => void }) {
  return (
    <div className="space-y-[15px]">
      {sections.map((section) => (
        <section key={section.id}>
          <h3 className="mb-[10px] h-5 text-xs font-bold leading-5 text-[#333]">
            {section.title}
          </h3>
          <div className="flex flex-wrap content-start">
            {section.items.map((item) => (
              <div key={item.id} className="m-[10px]">
                <MenuItemCard item={item} onNavigate={onNavigate} />
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

export function MegaMenu({ categories, isOpen, onClose }: MegaMenuProps) {
  const [activePanel, setActivePanel] = useState("hot");
  const sections = sectionsForPanel(activePanel, categories);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) {
    return null;
  }

  return (
    <>
      <button
        type="button"
        className="fixed inset-0 z-[60] cursor-default bg-black/50 backdrop-blur-[1px]"
        onClick={onClose}
        aria-label="Đóng danh mục"
      />

      <section
        role="dialog"
        aria-modal="true"
        aria-label="Danh mục sản phẩm và dịch vụ"
        className="absolute left-0 top-full z-[70] hidden h-[440px] w-[min(1007px,calc(100vw-17rem))] overflow-hidden rounded-b-lg bg-white text-[#333] shadow-2xl lg:flex"
      >
        <nav className="h-[440px] w-[230px] shrink-0 rounded-bl-lg bg-[#f2f4f7]">
          {megaMenuNavigation.map((item) => {
            const isActive = item.id === activePanel;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setActivePanel(item.id)}
                onMouseEnter={() => setActivePanel(item.id)}
                className={`flex h-10 w-[220px] items-center gap-2 overflow-hidden pl-3 pr-2 text-left text-sm leading-[18px] transition ${
                  isActive
                    ? "bg-white font-semibold text-[#0068d7]"
                    : "bg-[#eaecf0] text-[#333] hover:bg-[#f4f5f7]"
                }`}
                aria-pressed={isActive}
              >
                <span className="min-w-0 flex-1 whitespace-nowrap">{item.label}</span>
              </button>
            );
          })}
        </nav>
        <div className="h-[440px] min-w-0 flex-1 overflow-y-auto rounded-br-lg bg-white p-[10px]">
          <MenuContent sections={sections} onNavigate={onClose} />
        </div>
      </section>

      <section
        role="dialog"
        aria-modal="true"
        aria-label="Danh mục sản phẩm và dịch vụ"
        className="fixed inset-x-3 bottom-3 top-3 z-[70] flex flex-col overflow-hidden rounded-xl bg-white text-[#333] shadow-2xl lg:hidden"
      >
        <div className="flex h-14 shrink-0 items-center justify-between border-b border-slate-200 px-4">
          <h2 className="text-lg font-bold">Danh mục</h2>
          <button
            type="button"
            onClick={onClose}
            className="flex size-9 items-center justify-center rounded-full bg-slate-100 text-slate-600 transition hover:bg-slate-200 active:scale-95"
            aria-label="Đóng danh mục"
          >
            <X size={19} />
          </button>
        </div>
        <div className="scrollbar-none flex shrink-0 gap-2 overflow-x-auto border-b border-slate-200 bg-[#f2f4f7] p-2">
          {megaMenuNavigation.map((item) => {
            const isActive = item.id === activePanel;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setActivePanel(item.id)}
                className={`shrink-0 rounded-lg px-3 py-2 text-xs font-semibold transition ${
                  isActive ? "bg-white text-[#0068d7] shadow-sm" : "text-slate-600 hover:bg-white/70"
                }`}
                aria-pressed={isActive}
              >
                {item.label}
              </button>
            );
          })}
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto p-3 sm:p-4">
          <MenuContent sections={sections} onNavigate={onClose} />
        </div>
      </section>
    </>
  );
}
