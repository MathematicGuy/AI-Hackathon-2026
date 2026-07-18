"use client";
import type { ProductCitation } from "@/lib/types";
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

export function SourceDrawer({ citations }: { citations: ProductCitation[] }) {
  if (citations.length === 0) return null;
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button data-testid="source-drawer-trigger" className="bg-muted text-foreground">
          Nguồn & dẫn chứng ({citations.length})
        </Button>
      </DialogTrigger>
      <DialogContent data-testid="source-drawer-content">
        <DialogHeader>
          <DialogTitle>Nguồn dẫn chứng</DialogTitle>
        </DialogHeader>
        <ul className="flex flex-col gap-2 text-sm">
          {citations.map((c, i) => (
            <li key={`${c.product_id}-${c.field}-${i}`} className="border-b pb-2">
              <span className="font-medium">{c.field}</span>
              <a href={c.source_url} target="_blank" rel="noopener noreferrer" className="ml-2 text-primary underline">
                {c.source_url}
              </a>
            </li>
          ))}
        </ul>
      </DialogContent>
    </Dialog>
  );
}
