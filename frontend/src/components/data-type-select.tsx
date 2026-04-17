"use client"

import { Sprout, BanknoteIcon, Droplets, TreePine } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useTranslations } from "next-intl"
import { Card } from "@/components/ui/card"

interface DataTypeSelectProps {
  value: string
  onValueChange: (value: string) => void
}

export default function DataTypeSelect({ value, onValueChange }: DataTypeSelectProps) {
  const t = useTranslations("Alternative.variableTypes")
  return (
    <Select onValueChange={onValueChange} value={value}>
      <Card>
        <SelectTrigger className="w-full flex items-center justify-between shadow-none border-none">
          <SelectValue placeholder="Field data type" />
        </SelectTrigger>
      </Card>
      <SelectContent className="border-none shadow-none bg-transparent">
        <Card>
          <SelectItem value="crop">
            <div className="flex items-center space-x-2">
              <Sprout className="w-5 h-5 text-green-400" />
              <span>{t("crop")}</span>
            </div>
          </SelectItem>
          <SelectItem value="economy">
            <div className="flex items-center space-x-2">
              <BanknoteIcon className="w-5 h-5 text-emerald-600" />
              <span>{t("economy")}</span>
            </div>
          </SelectItem>
          <SelectItem value="nLoad">
            <div className="flex items-center space-x-2">
              <Droplets className="w-5 h-5 text-blue-600" />
              <span>{t("nLoad")}</span>
            </div>
          </SelectItem>
          <SelectItem value="nature">
            <div className="flex items-center space-x-2">
              <TreePine className="w-5 h-5 text-green-600" />
              <span>{t("nature")}</span>
            </div>
          </SelectItem>
        </Card>
      </SelectContent>
    </Select>
  )
}

