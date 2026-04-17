"use client";
import { useState } from "react";
import { ScaleIcon, ArrowUpIcon as ArrowTrendingUpIcon, GitCompare } from "lucide-react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

interface ToggleMapColorButtonProps {
  colorMode: string;
  onChange: (value: string) => void;
}

export default function ToggleMapColorButton({
  colorMode,
  onChange,
}: ToggleMapColorButtonProps) {
  const t = useTranslations("Alternative");
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  const toggleItems = [
    {
      value: "alternative",
      icon: <ArrowTrendingUpIcon className="h-4 w-4" />,
      label: t("alternative"),
      description: t("alternativeDescription"),
    },
    {
      value: "statusQuo",
      icon: <ScaleIcon className="h-4 w-4" />,
      label: t("statusquo"),
      description: t("statusQuoDescription"),
    },
    {
      value: "comparison",
      icon: <GitCompare className="h-4 w-4" />,
      label: t("difference"),
      description: t("comparisonDescription"),
    },
  ];

  return (
      <Tooltip>
        
          <Card className="cursor-pointer">
            <CardContent className="flex items-center justify-center gap-2 p-2">
            <TooltipTrigger asChild>
              <ToggleGroup type="single" value={colorMode} onValueChange={onChange}>
                {toggleItems.map((item) => (
                  <ToggleGroupItem
                    key={item.value}
                    value={item.value}
                    aria-label={item.label}
                    onMouseEnter={() => setHoveredItem(item.value)}
                    onMouseLeave={() => setHoveredItem(null)}
                  >
                    {item.icon}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
              </TooltipTrigger>
            </CardContent>
            <CardFooter className="flex flex-col items-center text-xs pb-2">
              <p>{t("fieldsShown")}:</p>
              <b>
                {toggleItems.find((item) => item.value === colorMode)?.label}
              </b>
            </CardFooter>
          </Card>
       
        <TooltipContent side="bottom">
          {hoveredItem
            ? toggleItems.find((item) => item.value === hoveredItem)?.description
            : toggleItems.find((item) => item.value === colorMode)?.description}
        </TooltipContent>
      </Tooltip>
  );
}
