"use client"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { type AlternativeModel } from "@/models/alternative"
import { Factory, FileSliders, Layers, Leaf, Map, Users, Wheat } from "lucide-react"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { motion } from "framer-motion"
import React from "react"

const iconColors = {
  biogas: "#FF6B6B",
  impact: "#4ECDC4",
  nature: "#45B649",
  area: "#4682B4",
  field: "#6E44FF",
  farm: "#FFD93D",
}

const getIconForName = (name: string) => {
  const nameLower = name.toLowerCase();
  
  if (nameLower.includes('biogas') || nameLower.includes('distance')) {
    return { Icon: Factory, color: iconColors.biogas };
  }
  if (nameLower.includes('farmer') || nameLower.includes('impact')) {
    return { Icon: Users, color: iconColors.impact };
  }
  if (nameLower.includes('nature')) {
    return { Icon: Leaf, color: iconColors.nature };
  }
  if (nameLower.includes('area')) {
    return { Icon: Map, color: iconColors.area };
  }
  if (nameLower.includes('field')) {
    return { Icon: Layers, color: iconColors.field };
  }
  if (nameLower.includes('farm')) {
    return { Icon: Wheat, color: iconColors.farm };
  }
  
  return null;
};

const renderConstraintIcon = (name: string) => {
  const iconData = getIconForName(name);
  if (!iconData) return null;
  
  const { Icon, color } = iconData;
  return (
    <div style={{ color }}>
      <Icon />
    </div>
  );
};

export default function ConstraintsDisplayCard({ alternativeModel }: { alternativeModel: AlternativeModel }) {
    const [hoveredItem, setHoveredItem] = useState<string | null>(null);
    const t = useTranslations("Alternative");
    const tFields = useTranslations("AlternativeFields");

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center space-x-2">
          <FileSliders className="h-6 w-6 text-primary" />
          <CardTitle className="text-xl font-bold">{t("constraints")}</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-3">
          {alternativeModel?.constraints ? (
            <>
          {Object.entries(alternativeModel?.constraints).map(([key, { enabled, value, name, unit }]) => (
            <TooltipProvider key={key} delayDuration={0}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div
                    className={`flex items-center justify-between rounded-lg p-2 transition-colors ${
                      enabled ? "bg-secondary/10" : ""
                    } ${hoveredItem === key ? "shadow-md" : ""}`}
                    onMouseEnter={() => setHoveredItem(key)}
                    onMouseLeave={() => setHoveredItem(null)}
                  >
                    <div className="flex gap-3 items-center">
                      {renderConstraintIcon(name)}
                      <span
                        className={`text-sm font-medium capitalize ${enabled ? "text-foreground" : "text-muted-foreground"}`}
                      >
                        {tFields("fieldNames." + name)}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`text-sm font-bold ${enabled ? "text-foreground" : "text-muted-foreground"}`}>
                        {value} {unit}
                      </span>
                      {!enabled && (
                        <Badge variant="outline" className="text-xs">
                          {t("disabled")}
                        </Badge>
                      )}
                    </div>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{tFields("fieldDescriptions." + name)}</p>
                </TooltipContent>
              </Tooltip>
              </TooltipProvider>
            ))}
            </>
          ) : (
            <div className="flex items-center justify-center">
              <p className="text-sm text-gray-500">{t("noConstraintData")}</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
    </motion.div>
  )
}

