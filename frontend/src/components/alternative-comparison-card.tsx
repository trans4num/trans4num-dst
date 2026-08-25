"use client";

import { type Alternative, type AlternativeResultSummaryEntry } from "@/models/alternative";
import { Blend, Box, FileSliders } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState, useMemo } from "react";
import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, type TooltipProps } from "recharts";
import { type NameType, type ValueType } from "recharts/types/component/DefaultTooltipContent";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Tooltip as RechartsTooltip } from "recharts";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { TabNavigation } from "@/components/tabs";
import ComparisonBarcharts from "@/components/comparison-barchart";
import { summaryColorPalette, statusQuoColor } from "@/lib/colors";

const ZERO_DECIMAL_SUMMARY_FIELDS = new Set([
  "economy",
  "consistency",
  "fieldConsistency",
  "farmEconomy",
  "nload",
]);

const UNIT_OVERRIDES: Record<string, string> = {
  nloadPerEcon: "kg N/1000 DKK",
};

const SCALE_OVERRIDES: Record<string, number> = {
  nloadPerEcon: 1000,
};

function displayUnit(item: ChartDataPoint): string {
  return UNIT_OVERRIDES[item.key] ?? item.unit;
}

function scaledValue(item: ChartDataPoint, rawValue: number): number {
  const scale = SCALE_OVERRIDES[item.key] ?? 1;
  return rawValue * scale;
}

const isStatusQuo = (alternative: Alternative, statusQuo: Alternative) => alternative.id === statusQuo.id;

interface AlternativeComparisonCardProps {
  selectedAlternatives: Alternative[];
  statusQuo: Alternative;
}

interface ChartDataPoint {
  key: string;
  name: string;
  fullMark: number;
  enabled: boolean;
  unit: string;
  [key: string]: number | string | boolean;
}

interface RawValuesMap {
  [alternativeId: string]: {
    [key: string]: number;
  };
}

export default function AlternativeComparisonCard({
  selectedAlternatives,
  statusQuo,
}: AlternativeComparisonCardProps) {
  const t = useTranslations("AlternativeComparisonCard");
  const tFields = useTranslations("AlternativeFields");

  const combinedAlternatives = useMemo(() => 
    [...selectedAlternatives, statusQuo],
    [selectedAlternatives, statusQuo]
  );

  const { summaryChartData, summaryChartFractionData, constraintChartData, rawValues } = useMemo(() => {
    if (selectedAlternatives.length === 0 || !statusQuo) {
      return {
        summaryChartData: [],
        summaryChartFractionData: [],
        constraintChartData: [],
        rawValues: {}
      };
    }

    const generateChartData = (
      alternatives: Alternative[],
      dataPoints: ChartDataPoint[],
      getValue: (alt: Alternative, key: string) => number,
      fraction: boolean = false,
    ) => {
      const rawValuesMap: RawValuesMap = {};

      const chartData = dataPoints.map((item) => {
        const entry: ChartDataPoint = {
          key: item.key,
          name: item.name,
          fullMark: item.fullMark,
          unit: item.unit,
          enabled: item.enabled,
        };

        const statusQuoValue = getValue(statusQuo, item.key);

        alternatives.forEach((alt) => {
          if (!rawValuesMap[alt.id]) {
            rawValuesMap[alt.id] = {};
          }

          const altValue = getValue(alt, item.key);
          rawValuesMap[alt.id][item.key] = altValue;

          if (statusQuoValue === 0 || !fraction) {
            entry[alt.id] = altValue;
          } else {
            entry[alt.id] = altValue / statusQuoValue;
          }
        });

        return entry;
      });

      return { chartData, rawValuesMap };
    };

    const summaryDataPoints: ChartDataPoint[] = (statusQuo?.summary ?? []).map((item: AlternativeResultSummaryEntry) => ({
      key: item.name,
      name: tFields("fieldNames." + item.name),
      fullMark: 1,
      unit: item.unit,
      enabled: true,
    }));

    const constraintDataPoints = Array.from(
      new Map(
        selectedAlternatives
          .flatMap(alt => alt.model?.constraints ?? [])
          .map(c => [
            c.name,
            {
              key: c.name,
              name: tFields("fieldNames." + c.name),
              fullMark: 100,
              unit: c.unit ?? "",
              enabled: c.enabled,
            }
          ])
      ).values()
    );

    const { chartData: summaryData, rawValuesMap: summaryRawValues } = generateChartData(
      combinedAlternatives,
      summaryDataPoints,
      (alt, key) => alt.summary?.find(item => item.name === key)?.value ?? 0,
    );
    const { chartData: summaryFractionData } = generateChartData(
      combinedAlternatives,
      summaryDataPoints,
      (alt, key) => alt.summary?.find(item => item.name === key)?.value ?? 0,
      true
    );

    const { chartData: constraintData } = generateChartData(
      selectedAlternatives,
      constraintDataPoints,
      (alt, key) =>
        alt.model?.constraints.find(c => c.name === key)?.value ?? 0
    );

    // Merge raw values from both charts
    const combinedRawValues: RawValuesMap = {};
    selectedAlternatives.forEach((alt) => {
      combinedRawValues[alt.id] = {
        ...summaryRawValues[alt.id],
      };
    });

    return {
      summaryChartData: summaryData,
      summaryChartFractionData: summaryFractionData,
      constraintChartData: constraintData,
      rawValues: combinedRawValues
    };
  }, [selectedAlternatives, statusQuo, tFields, combinedAlternatives]);

  const hasData = summaryChartData.length > 0 && selectedAlternatives.length > 0 && statusQuo !== null;
  const hasConstraintData = constraintChartData.length > 0 && selectedAlternatives.length > 0 && statusQuo !== null;
  const hasBarChartData = useMemo(() => 
    selectedAlternatives.length > 0 &&
    statusQuo !== null &&
    [...(statusQuo.barCharts ?? []), ...selectedAlternatives.flatMap((a) => a.barCharts ?? [])].length > 0
    , [selectedAlternatives, statusQuo]);

  const CustomTooltip = ({ active, payload, label }: TooltipProps<ValueType, NameType>) => {
    if (active && payload && payload.length && statusQuo) {
      const dataKey = summaryChartData.find((item) => item.name === label)?.key ||
        constraintChartData.find((item) => item.name === label)?.key || "";

      return (
        <div className="bg-white p-3 shadow-md rounded-md border border-gray-200">
          <p className="text-gray-700 font-medium mb-2">{label as string}</p>
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-1"></th>
                <th className="text-right py-1 px-2">{t("raw")}</th>
                <th className="text-right py-1 px-2">{t("statusQuo")}</th>
                <th className="text-right py-1 px-2">{t("ratio")}</th>
              </tr>
            </thead>
            <tbody>
              {payload.map((entry, index) => {
                const altId = entry.dataKey as string;
                const rawValue = rawValues[altId]?.[dataKey] || 0;
                const statusQuoValue = statusQuo.summary?.find(item => item.name === dataKey)?.value ??
                  statusQuo.model?.constraints.find(c => c.name === dataKey)?.value ?? 0;
                const ratio = typeof rawValue === 'number' && typeof statusQuoValue === 'number'
                  ? (rawValue / statusQuoValue).toFixed(2)
                  : "N/A";

                return (
                  entry.dataKey !== statusQuo.id && (
                  <tr key={`item-${index}`} className="border-b last:border-b-0">
                    <td className="py-1">
                      <div className="flex items-center">
                        <div
                          className="w-3 h-3 rounded-full mr-2"
                          style={{ backgroundColor: entry.color }}
                        ></div>
                        <span className="font-medium">{entry.name as string}</span>
                      </div>
                    </td>
                    <td className="text-right py-1 px-2">
                      {typeof rawValue === 'number' ? rawValue.toFixed(2) : rawValue}
                    </td>
                    <td className="text-right py-1 px-2">
                      {typeof statusQuoValue === 'number' ? statusQuoValue.toFixed(2) : statusQuoValue}
                    </td>
                    <td className="text-right py-1 px-2">{ratio}</td>
                  </tr>
                  )
                );
              })}
            </tbody>
          </table>
        </div>
      );
    }
    return null;
  };

  return (
      <div className="p-6 overflow-y-auto max-h-[calc(100vh-8rem)]">
        <div className="flex flex-col items-left justify-between mb-6">
          <div className="flex items-center justify-start mb-0">
            <Blend className="h-6 w-6 mr-2" />
            <h3 className="text-2xl font-bold mb-0">{t("cardTitle")}</h3>
          </div>
          <div className="flex items-center">
            <CustomLegend
              alternatives={combinedAlternatives}
              statusQuo={statusQuo}
              colorPalette={summaryColorPalette}
            />
          </div>
        </div>
        <div className="flex flex-col gap-6">
          <ConstraintChart
            constraintChartData={constraintChartData}
            alternatives={selectedAlternatives}
            statusQuo={statusQuo}
            hasData={hasConstraintData}
          />
          <SummaryChart
            summaryChartData={summaryChartData}
            summaryChartFractionData={summaryChartFractionData}
            combinedAlternatives={combinedAlternatives}
            statusQuo={statusQuo}
            hasData={hasData}
            customTooltip={CustomTooltip}
          />
          <ComparisonBarcharts 
          alternatives={combinedAlternatives} 
          hasData={hasBarChartData} />
        </div>
      </div>
  );
}

type ContentType<V extends ValueType, N extends NameType> =
  React.ReactElement |
  ((props: TooltipProps<V, N>) => React.ReactNode);

interface ChartSectionProps {
  data: ChartDataPoint[];
  alternatives: Alternative[];
  statusQuo: Alternative;
  hasData: boolean;
  customTooltip?: ContentType<ValueType, NameType>;
  orientation?: "vertical" | "horizontal";
  colorDisplay?: "background" | "dot";
}

function TableSection({
  data,
  alternatives,
  statusQuo,
  hasData,
  orientation = "vertical",
  colorDisplay = "background",
}: ChartSectionProps) {
  const t = useTranslations("AlternativeComparisonCard");
  const tFields = useTranslations("AlternativeFields");
  return (
    <>
      {hasData ? (
        <div className="rounded-lg overflow-scroll border border-gray-200">
          <table className="min-w-full text-sm">
            {orientation === "vertical" ? (
              <>
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    {colorDisplay === "dot" && (
                      <th className="py-2 px-3 font-medium"></th>
                    )}
                    {data.map((item) => (
                      <Tooltip key={item.key}>
                        <TooltipTrigger asChild>
                      <th key={item.key} className={`py-2 px-3 font-medium text-left border-r last:border-r-0`}>
                        {tFields("fieldNames." + item.key)}
                        {displayUnit(item) && <span className="text-xs ml-1">({displayUnit(item)})</span>}
                      </th>
                      </TooltipTrigger>
                      <TooltipContent side="top">
                        {tFields("fieldDescriptions." + item.key)}
                      </TooltipContent>
                      </Tooltip>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {alternatives.map((alt, index) => (
                    <tr
                      key={alt.id}
                      className="border-b last:border-b-0"
                    >
                      {colorDisplay === "dot" && (
                        <td className="py-2 px-3 font-medium">
                          <div className="flex items-center">
                            <div className="min-w-2 min-h-2 rounded-full mr-2" 
                            style={{ backgroundColor: `${isStatusQuo(alt, statusQuo) 
                            ? statusQuoColor 
                            : summaryColorPalette[index % summaryColorPalette.length]}` }} />
                            {alt.name}
                          </div>
                        </td>
                      )}
                      {data.map((item) => (
                        <td
                          key={`${item.key}-${alt.id}`}
                          className={`text-right py-2 px-3 border-r last:border-r-0 ${item.enabled ? "" : "opacity-50 line-through"}`}
                          style={{ backgroundColor: `${colorDisplay === "background" 
                            ? isStatusQuo(alt, statusQuo) ? statusQuoColor + "30" 
                              : summaryColorPalette[index % summaryColorPalette.length] + "30" 
                            : "transparent"}` }}
                        >
                          {typeof item[alt.id] === 'number' && !isNaN(item[alt.id] as number)
                            ? scaledValue(item, item[alt.id] as number).toLocaleString('da-DK', { 
                              maximumFractionDigits: ZERO_DECIMAL_SUMMARY_FIELDS.has(item.key) ? 0 : 2,
                            })
                            : item[alt.id]}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </>
            ) : (
              <tbody>
                {data.map((item) => (
                  <tr key={item.key} className="border-b last:border-b-0">
                    <td className="py-2 px-3 font-medium">{item.name}</td>
                    {alternatives.map((alt, index) => (
                      <td
                        key={`${item.key}-${alt.id}`}
                        className="text-right py-2 px-3"
                        style={{ backgroundColor: `${isStatusQuo(alt, statusQuo) 
                            ? statusQuoColor + "30" 
                            : summaryColorPalette[index % summaryColorPalette.length] + "30"}` }}
                      >
                        {typeof item[alt.id] === 'number' && !isNaN(item[alt.id] as number)
                          ? scaledValue(item, item[alt.id] as number).toLocaleString('da-DK', { 
                            maximumFractionDigits: ZERO_DECIMAL_SUMMARY_FIELDS.has(item.key) ? 0 : 2,
                          })
                          : item[alt.id]}
                        {displayUnit(item) && <span className="text-xs ml-1">{item.unit}</span>}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            )}
          </table>
        </div>
      ) : (
        <div className="flex items-center justify-center h-64 text-gray-500">
          <p>{t("noConstraintData")}</p>
        </div>
      )}
    </>
  );
}

function RadarSection({
  data,
  alternatives,
  statusQuo,
  hasData,
  customTooltip,
}: ChartSectionProps) {
  const t = useTranslations("AlternativeComparisonCard");
  const maxValue = Math.ceil(Math.max(...data.flatMap(item => 
    alternatives.map(alt => item[alt.id] as number ?? 0)
  )) * 2) / 2;
  const tickCount = maxValue * 2 + 1;

  return (
    <div>
      {hasData ? (
        <ResponsiveContainer width="100%" height={250}>
          <RadarChart data={data}>
            <PolarGrid />
            <PolarAngleAxis dataKey="name" tick={{ fill: "black" }} />
            <PolarRadiusAxis angle={60} domain={[0, maxValue]} tick={{ fill: "black" }} tickCount={tickCount} />
            {customTooltip ? <RechartsTooltip content={customTooltip} /> : <RechartsTooltip />}
            {alternatives.map((alt, idx) => (
              <Radar
                key={alt.id}
                name={alt.name}
                dataKey={alt.id}
                stroke={isStatusQuo(alt, statusQuo) ? statusQuoColor : summaryColorPalette[idx % summaryColorPalette.length]}
                fill={isStatusQuo(alt, statusQuo) ? statusQuoColor : summaryColorPalette[idx % summaryColorPalette.length]}
                fillOpacity={0.3}
              />
            ))}
          </RadarChart>
        </ResponsiveContainer>
      ) : (
        <div className="flex items-center justify-center h-64 text-gray-500">
          <p>{t("selectAlternative")}</p>
        </div>
      )}
    </div>
  );
}

interface ConstraintChartProps {
  constraintChartData: ChartDataPoint[];
  alternatives: Alternative[];
  statusQuo: Alternative;
  hasData: boolean;
}

function ConstraintChart({ constraintChartData, alternatives, statusQuo, hasData }: ConstraintChartProps) {
  const t = useTranslations("AlternativeComparisonCard");

  return <Card>
    <CardHeader>
      <div className="flex">
        <div className="flex items-center">
          <FileSliders className="h-6 w-6 mr-2" />
          <h4 className="text-lg font-semibold">{t("constraintsTitle")}</h4>
        </div>
      </div>
    </CardHeader>
    <CardContent>
      <TableSection
        data={constraintChartData}
        alternatives={alternatives}
        statusQuo={statusQuo}
        hasData={hasData}
      />
    </CardContent>
  </Card>
}

interface SummaryChartProps {
  summaryChartData: ChartDataPoint[];
  summaryChartFractionData: ChartDataPoint[];
  combinedAlternatives: Alternative[];
  statusQuo: Alternative;
  hasData: boolean;
  customTooltip: ContentType<ValueType, NameType>;
}

function SummaryChart({ summaryChartData, summaryChartFractionData, combinedAlternatives, statusQuo, hasData, customTooltip }: SummaryChartProps) {
  const t = useTranslations("AlternativeComparisonCard");
  const [summaryIsTable, setSummaryIsTable] = useState(false);

  return <Card>
    <CardHeader>
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Box className="h-6 w-6 mr-2" />
          <h4 className="text-lg font-semibold">{t("summaryTitle")}</h4>
        </div>
        <TabNavigation
          tabs={[
            { key: "radar", displayValue: t("radarView") },
            { key: "table", displayValue: t("tableView") },
          ]}
          onTabChange={(index) => setSummaryIsTable(index === 1)}
          initialIndex={0}
        />
      </div>
    </CardHeader>
    <CardContent>
      {summaryIsTable ? (
        <TableSection
          data={summaryChartData}
          alternatives={combinedAlternatives}
          statusQuo={statusQuo}
          hasData={hasData}
        />
      ) : (
        <RadarSection
          data={summaryChartFractionData}
          alternatives={combinedAlternatives}
          statusQuo={statusQuo}
          hasData={hasData}
          customTooltip={customTooltip}
        />
      )}
    </CardContent>
  </Card>
}


interface CustomLegendProps {
  alternatives: Alternative[];
  statusQuo: Alternative;
  colorPalette: string[];
}

function CustomLegend({ alternatives, statusQuo, colorPalette }: CustomLegendProps) {
  return (
    <div className="flex flex-row flex-wrap gap-4 mt-6">
      {alternatives.map((alt, index) => (
        <div
          key={alt.id}
          className="flex items-center justify-between p-3 bg-white shadow rounded-lg"
        >
          <div className="flex items-center">
            <div
              className="w-4 h-4 rounded-full mr-3"
              style={{
                backgroundColor: isStatusQuo(alt, statusQuo) ? statusQuoColor : colorPalette[index % colorPalette.length],
              }}
            ></div>
            <div>
              <h5 className="text-sm font-medium">{alt.name}</h5>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
