"use client"

import { ArrowUpIcon as ArrowTrendingUpIcon, ScaleIcon, Sprout, BanknoteIcon, Droplets } from "lucide-react"
import { Card } from "@/components/ui/card"

interface HoverCardProps {
  x: number
  y: number
  dataType: string
  alternative: {
    value: string
    color: string
  }
  statusQuo: {
    value: string
    color: string
  }
}

export default function HoverInfoCard({ x, y, dataType, alternative, statusQuo }: HoverCardProps) {
  const getTypeIcon = () => {
    switch (dataType.toLowerCase()) {
      case "crop":
        return <Sprout className="w-6 h-6 text-green-600" />
      case "economy":
        return <BanknoteIcon className="w-6 h-6 text-emerald-600" />
      case "nload":
        return <Droplets className="w-6 h-6 text-blue-600" />
      default:
        return null
    }
  }

  return (
    <Card
      className="absolute z-50 bg-white p-4 rounded-lg shadow-lg w-[300px]"
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
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gray-200" />
      </div>

      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <ArrowTrendingUpIcon className="w-5 h-5 text-blue-500" />
          <div className="flex items-center justify-between flex-1">
            <div>
              <div className="text-sm font-medium text-gray-500">Alternative</div>
              <div className="font-semibold">{alternative.value}</div>
            </div>
            <div className="w-5 h-5 rounded-full" style={{ backgroundColor: alternative.color }} />
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <ScaleIcon className="w-5 h-5 text-gray-600" />
          <div className="flex items-center justify-between flex-1">
            <div>
              <div className="text-sm font-medium text-gray-500">Status Quo</div>
              <div className="font-semibold">{statusQuo.value}</div>
            </div>
            <div className="w-5 h-5 rounded-full" style={{ backgroundColor: statusQuo.color }} />
          </div>
        </div>
      </div>
    </Card>
  )
}

