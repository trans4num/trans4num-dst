"use client";

import { useTranslations } from "next-intl";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Text,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { Props as RechartsTextProps } from "recharts/types/component/Text";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { ChartBarBig } from "lucide-react";
import type { Alternative, AlternativeBarChart } from "@/models/alternative";
import { valueRangeForChartData, ticksForValueRange } from "@/lib/helpers/barchart-axis-helpers";
import { barchartColorPalette } from "@/lib/colors";
import { useMemo } from "react";

type AxisTickProps = RechartsTextProps & {
  payload: { value: string | number };
};

const CustomYAxisTick = (props: AxisTickProps) => {
  const { payload, ...rest } = props;
  const num = Number(payload.value);

  let fill: string;
  switch (Math.sign(num)) {
    case -1:
      fill = "red";
      break;
    default:
      fill = "black";
  }

  return (
    <Text {...rest} fill={fill} fontWeight={num === 0 ? "bold" : "normal"}>
      {num.toLocaleString("da-DK", { maximumFractionDigits: 2 })}
    </Text>
  );
};

type BarChartWithAlternativeName = AlternativeBarChart & {
  alternativeName: string
}

interface ComparisonBarchartProps {
  alternatives: Alternative[]
  hasData: boolean
}

export default function ComparisonBarcharts( { alternatives, hasData: hasData }: ComparisonBarchartProps ) {
  const barChartsGroupedByChartName = useMemo(() => {
    const allBarCharts = alternatives.flatMap((alternative) => alternative.barCharts?.map(barChart => ({ ...barChart, alternativeName: alternative.name })) ?? []);
    return allBarCharts
      .reduce<Record<string, BarChartWithAlternativeName[]>>((accumulator, chart) => {
        const name = chart.chartName;
        if (!accumulator[name]) accumulator[name] = [];
        accumulator[name].push(chart);
        return accumulator;
      }, {});
  }, [alternatives]);

  const groupedEntries = Object.entries(barChartsGroupedByChartName);

  if (!hasData || groupedEntries.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-6">
      {groupedEntries.map(([name, charts]) => (
        <BarChartCard key={name} charts={charts} />
      ))}
    </div>
  );
}

function BarChartCard( { charts }: { charts: BarChartWithAlternativeName[] } ) {
  const t = useTranslations("AlternativeComparisonCard");
  const title = charts[0]?.chartName ?? "";
  const isNBalance = title === "N-Balance";

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center">
          <ChartBarBig className="size-6 mr-2 rotate-270" />
          <h4 className="text-lg font-semibold">{title}</h4>
        </div>

        {isNBalance && (
          <p className="text-xs text-muted-foreground whitespace-pre-line mt-2">
            {t("nbalanceDescription")}
          </p>
        )}
      </CardHeader>
      <CardContent className="flex w-full flex-col gap-4">
        {charts.map((barChart, index) => (
          <div key={index}>{renderBarChart(barChart)}</div>
        ))}
      </CardContent>
    </Card>
  );
}

function renderBarChart(barChart: BarChartWithAlternativeName) {
  const chartData = barChart.chartData;
  const valueRange = valueRangeForChartData(chartData);
  const yAxisTicks = ticksForValueRange(valueRange);
  const yAxisDomain: [number, number] = [
    yAxisTicks[0],
    yAxisTicks[yAxisTicks.length - 1],
  ];

  return (
    <div className="w-full space-y-3">
      <AlternativeFacetTitle name={barChart.alternativeName} />
      <div className="flex w-full flex-row flex-wrap">
        {chartData.map((category) => {
          const valueKeys = Object.keys(category.values);
          const data = [{ name: category.name, ...category.values }];
          return (
            <div
              key={category.name}
              className="h-[400px] min-w-[12rem] flex-1 basis-0 border-b border-border pb-2"
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={data}
                  margin={{
                    top: 5,
                    right: 0,
                    left: 0,
                    bottom: 5,
                  }}
                >
                  <CartesianGrid strokeOpacity={0.5}/>
                  <XAxis dataKey="name" />
                  <YAxis
                    type="number"
                    width={100}
                    tick={CustomYAxisTick}
                    domain={yAxisDomain}
                    ticks={yAxisTicks}
                    allowDecimals
                  />
                  <Tooltip />
                  <Legend />
                  <ReferenceLine y={0} stroke="#000" />
                  {valueKeys.map((key, index) => {
                    const color = barchartColorPalette[index % barchartColorPalette.length];
                    return (
                      <Bar
                        key={key}
                        dataKey={key}
                        unit={barChart.unit}
                        fill={color}
                        fillOpacity={0.45}
                        stroke={color}
                        strokeWidth={1}
                        radius={[5, 5, 0, 0]}
                      />
                    );
                  })}
                </BarChart>
              </ResponsiveContainer>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function AlternativeFacetTitle({ name }: { name: string }) {
  const t = useTranslations("Alternative");

  return (
    <div className="w-full pb-2">
      <div className="flex w-full flex-wrap items-baseline gap-x-2 gap-y-0.5">
        <span className="text-sm font-medium text-muted-foreground">
          {t("alternative")}
        </span>
        <span className="text-md font-semibold tracking-tight text-foreground">{name}</span>
      </div>
    </div>
  );
}
