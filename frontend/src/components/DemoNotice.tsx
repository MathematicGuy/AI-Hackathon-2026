import { Info } from "lucide-react";

/**
 * Marks a flow that is a demonstration rather than a working feature.
 *
 * Login, checkout, and order history have no backend: nothing is
 * authenticated, no order is placed, and no order history is real. The banner
 * makes that explicit so a deployed build cannot be mistaken for a functioning
 * storefront.
 */
export function DemoNotice({ children }: { children: React.ReactNode }) {
  return (
    <p
      role="note"
      data-testid="demo-notice"
      className="mb-5 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-[13px] leading-5 text-amber-900"
    >
      <Info className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
      <span>
        <strong className="font-bold">Bản demo:</strong> {children}
      </span>
    </p>
  );
}
