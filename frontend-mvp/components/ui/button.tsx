import * as React from "react";
import { cn } from "@/lib/utils";

export const Button = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement>
>(({ className, ...props }, ref) => (
  <button
    ref={ref}
    className={cn(
      "inline-flex items-center justify-center rounded-md border bg-primary px-3 py-2 text-sm font-medium text-primary-foreground",
      "disabled:opacity-50 disabled:pointer-events-none",
      className,
    )}
    {...props}
  />
));
Button.displayName = "Button";
