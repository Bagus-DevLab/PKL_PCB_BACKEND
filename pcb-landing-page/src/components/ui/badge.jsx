import * as React from "react"
import { cva } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
    "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
    {
        variants: {
            variant: {
                default:
                    "border-transparent bg-pcb-primary text-white shadow hover:bg-pcb-primary/80",
                secondary:
                    "border-transparent bg-pcb-secondary text-white hover:bg-pcb-secondary/80",
                destructive:
                    "border-transparent bg-red-500 text-white shadow hover:bg-red-500/80",
                outline: "text-foreground border-pcb-sage/50",
                success: "border-transparent bg-pcb-mint text-pcb-primary shadow hover:bg-pcb-mint/80",
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
