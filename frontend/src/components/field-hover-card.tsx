"use client"

import { Card } from "@/components/ui/card"
import { ArrowUpIcon as ArrowTrendingUpIcon, BanknoteIcon, Droplets, ScaleIcon, Sprout, TreePine } from "lucide-react"
import { Separator } from "@/components/ui/separator"
import { useTranslations } from "next-intl"

interface HoverCardProps {
  x: number
  y: number
  dataType: string
  fieldId: string;
  alternativeValue: string;
  statusQuoValue:string;
}

export default function HoverInfoCard({ x, y, dataType, fieldId, alternativeValue, statusQuoValue }: HoverCardProps) {
  const t = useTranslations("Alternative");

  const getTypeIcon = () => {
    switch (dataType.toLowerCase()) {
      case "crop":
        return <Sprout className="w-6 h-6 text-green-400" />
      case "economy":
        return <BanknoteIcon className="w-6 h-6 text-emerald-600" />
      case "nload":
        return <Droplets className="w-6 h-6 text-blue-600" />
        case "nature":
        return <TreePine className="w-6 h-6 text-green-600" />
      default:
        return null
    }
  }

  const getMetric = () => {
    switch (dataType.toLowerCase()) {
      case "economy":
        return "kr/ha"
      case "nload":
        return "kg/ha"
        case "nature":
        return "%"
      default:
        return null
    }
  }

  return (
    <Card
      className="absolute z-50 bg-white p-4 rounded-lg shadow-lg"
      style={{
        left: x + 10,
        top: y + 10,
      }}
    >
      <div className="relative mb-4">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold text-gray-900 capitalize">{dataType}</h1>
          <div className="flex items-center justify-center">{getTypeIcon()}</div>
        </div>
        <Separator />
      </div>

      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <ArrowTrendingUpIcon className="w-5 h-5 text-blue-500" />
          <div className="flex items-center justify-between flex-1">
            <div>
              <div className="text-sm font-medium text-gray-500">{t("alternative")}</div>
              <div className="font-semibold">{alternativeValue} {getMetric()}</div>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <ScaleIcon className="w-5 h-5 text-gray-600" />
          <div className="flex items-center justify-between flex-1">
            <div>
              <div className="text-sm font-medium text-gray-500">{t("statusquo")} </div>
              <div className="font-semibold">{statusQuoValue} {getMetric()}</div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}
