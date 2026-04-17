import { cn } from "@/lib/utils";
import { ChevronDown, ScrollText } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { ColorScheme } from "@/lib/colors";
import { useMemo } from "react";

interface FieldMetadataLegendProps {
  type: "categorical" | "numeric";
  values: Record<string, string>;
  minValue?: number;
  maxValue?: number;
  colorScheme: ColorScheme;
  getColor: (value: number, min: number, max: number, scheme: ColorScheme) => string;
}

export default function FieldMetadataLegend({
  type,
  values,
  minValue = 0,
  maxValue = 100,
  colorScheme = "redToGreen",
  getColor,
}: FieldMetadataLegendProps) {
  const t = useTranslations("Alternative");
  const [isOpen, setIsOpen] = useState(true);

  const getColorAtPosition = useMemo(() => {
    const startColor = getColor(minValue, minValue, maxValue, colorScheme);
    const middleColor = getColor((minValue + maxValue) / 2, minValue, maxValue, colorScheme);
    const endColor = getColor(maxValue, minValue, maxValue, colorScheme);

    return `linear-gradient(0deg, ${startColor} 0%, ${middleColor} 50%, ${endColor} 100%)`;
  }, [minValue, maxValue, colorScheme, getColor]);

  return (
    <Card className="h-full flex flex-col p-4">
      <CardHeader className="p-0">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full flex items-center justify-between text-sm font-medium hover:text-gray-700 transition-colors"
        >
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center">
              <ScrollText className="h-4 w-4 mr-2" /> {t("legendTitle")}
            </div>
            <ChevronDown
              className={cn(
                "h-4 w-4 transition-transform duration-200",
                isOpen && "transform rotate-180"
              )}
            />
          </div>
        </button>
      </CardHeader>
      <CardContent className="flex-1 min-h-0 p-0">
        <div className="h-full">
          <div
            className={cn(
              "grid transition-all duration-200 ease-in-out h-full",
              isOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
            )}
          >
            <div className="min-h-0 h-full flex flex-col">
              <Separator className="my-2" />
              <div className="min-h-0 overflow-auto h-full">
                {type === "categorical" ? (
                  <div className="flex flex-col gap-2">
                    {Object.entries(values).sort(([keyA], [keyB]) => keyA.localeCompare(keyB)).map(([key, value]) => (
                      <div key={key} className="flex items-center gap-2">
                        <span
                          className="rounded-full w-4 h-4"
                          style={{ backgroundColor: value }}
                        />
                        <p className="text-xs text-wrap max-w-[5vw]">{key}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center flex-col gap-2 pt-4">
                    <span className="text-xs text-gray-600 flex flex-col items-center"><p>{t("maxValue")}</p><b>{maxValue}</b></span>

                    <div
                      className="w-3 h-[30vh] rounded-full relative cursor-pointer"
                      style={{ background: getColorAtPosition }}
                    />

                    <span className="text-xs text-gray-600 flex flex-col items-center"><p>{t("minValue")}</p><b>{minValue}</b></span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
