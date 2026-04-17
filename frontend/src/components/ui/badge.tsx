import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { CheckCircle, Loader2, XCircle, CircleCheck } from "lucide-react"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground shadow hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground shadow hover:bg-destructive/80",
        success:
          "select-none border-transparent items-center gap-2 rounded-lg bg-green-100 px-4 py-2 text-green-600 hover:bg-green-200",
        pending:
          "select-none border-transparent items-center gap-2 rounded-lg bg-yellow-100 px-4 py-2 text-yellow-600 hover:bg-yellow-200",
        outline: "text-foreground",
        failed:
          "select-none border-transparent items-center gap-2 rounded-lg bg-red-100 px-4 py-2 text-red-600 hover:bg-red-200",
        nonOptimal:
          "select-none border-transparent items-center gap-2 rounded-lg bg-teal-100 px-4 py-2 text-teal-600 hover:bg-teal-200",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props}>
      {variant === "success" && <CheckCircle className="size-4" />}
      {variant === "pending" && <Loader2 className="size-4 animate-spin" />}
      {variant === "failed" && <XCircle className="size-4" />}
      {variant === "nonOptimal" && <CircleCheck className="size-4" />}
      {props.children}
    </div>
  )
}

export { Badge, badgeVariants }
