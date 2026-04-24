import * as React from "react"
import { cva } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
    "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
    {
        variants: {
            variant: {
                default:
                    "border-transparent bg-pcb-blue text-pcb-light shadow hover:bg-pcb-blue/80",
                secondary:
                    "border-transparent bg-pcb-dark text-pcb-light hover:bg-pcb-dark/80",
                destructive:
                    "border-transparent bg-red-500 text-slate-50 shadow hover:bg-red-500/80",
                outline: "text-foreground",
                success: "border-transparent bg-pcb-green text-pcb-dark shadow hover:bg-pcb-green/80",
            },
        },
        defaultVariants: {
            variant: "default",
        },
    }
)

function Badge({
    className,
    variant,
    ...props
}) {
    return (
        (<div className={cn(badgeVariants({ variant }), className)} {...props} />)
    );
}

export { Badge, badgeVariants }
