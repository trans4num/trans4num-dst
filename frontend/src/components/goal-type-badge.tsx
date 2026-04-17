import type React from "react"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, BarChart2, Sprout, Box } from "lucide-react"
import { type AlternativeGoal } from "@/models/alternative"
import { camelCaseToSpaced } from "@/lib/helpers/string-helpers"
import { useTranslations } from "next-intl"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"

const getGoalTypeStyles = (goalType?: string): { color: string; icon: React.ReactNode; name: string } => {
  const styles: Record<string, { color: string; icon: React.ReactNode }> = {
    maximizeEconomy: {
      color: "bg-blue-100 text-blue-800 hover:bg-blue-200",
      icon: <TrendingUp />
    },
    maximizeEconomyNLoad: {
      color: "bg-yellow-100 text-yellow-800 hover:bg-yellow-200",
      icon: <BarChart2 />
    },
    minimizeNLoad: {
      color: "bg-purple-100 text-purple-800 hover:bg-purple-200",
      icon: <Sprout />
    },
  }
  
  const defaultStyle = {
    color: "bg-gray-100 text-gray-800 hover:bg-gray-200",
    icon: <Box />
  }
  
  const style = goalType ? (styles[goalType] ?? defaultStyle) : defaultStyle
  const name = goalType ? (camelCaseToSpaced(goalType) || "Unknown") : "Unknown"
  
  return { ...style, name }
}

interface GoalTypeBadgeProps {
  goal?: AlternativeGoal
}

export function GoalTypeBadge({ goal }: GoalTypeBadgeProps) {
  const { color, icon } = getGoalTypeStyles(goal?.type)
  const t = useTranslations("HomePage.columns")
  
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge variant="secondary" className={`inline-flex gap-2 items-center px-4 py-2 text-sm font-medium ${color}`}>
          <div className="flex items-center min-w-4 min-h-4 max-w-4 max-h-4">
            {icon}
          </div>
          <span className="sr-only">Goal Type:</span>
          {t("goalType." + goal?.type)}
        </Badge>
      </TooltipTrigger>
      <TooltipContent>
       {t("goalTypeLong." + goal?.type)}
      </TooltipContent>
    </Tooltip>
  )
}

