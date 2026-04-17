import {type LucideIcon } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"

interface GoalTypeCardProps {
  icon: LucideIcon
  title: string
  description: string
  selected: boolean
  onClick: () => void
}

export function GoalTypeCard({ icon: Icon, title, description, selected, onClick }: GoalTypeCardProps) {
  return (
    <Card
      className={`cursor-pointer transition-all h-max ${selected ? "border-green-500 border-2" : "hover:border-gray-300"}`}
      onClick={onClick}
    >
      <CardContent className="p-6 gap-4">
        <div className="flex items-center space-x-4">
          <Icon className="h-8 w-8 text-gray-500" aria-hidden="true" />
          <div>
            <h3 className="font-semibold">{title}</h3>
            <p className="text-sm text-gray-500">{description}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

