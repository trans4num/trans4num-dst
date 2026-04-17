"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { type Alternative } from "@/models/alternative"
import { Bean, Flower2, LucidePieChart, Package, RotateCcw, Sprout, Wheat } from "lucide-react"
import { useTranslations } from "next-intl"
import { motion } from "framer-motion"
import { Cell, Pie, PieChart, type PieLabelRenderProps } from "recharts"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ChevronDown } from "lucide-react"
import { useRef, useState, useMemo } from "react"
import { type AlternativeChart } from "@/models/alternative"
import { Separator } from "@/components/ui/separator"
import { hsvToRgb } from "@/lib/colors"
import { camelCaseToTitle } from "@/lib/helpers/string-helpers"

const getChartIcon = (key?: string): React.ReactNode => {
    if (!key) {
        return <Package className="w-4 h-4" />;
    }
    const lowerKey = key.toLowerCase();
    if (['crop', 'grass', 'plant'].some(term => lowerKey.includes(term))) {
        return <Sprout className="w-4 h-4" />;
    }
    if (['wheat', 'corn', 'maize', 'cereal'].some(term => lowerKey.includes(term))) {
        return <Wheat className="w-4 h-4" />;
    }
    if (['rape'].some(term => lowerKey.includes(term))) {
        return <Flower2 className="w-4 h-4" />;
    }
    if (['bean', 'legume', 'potato'].some(term => lowerKey.includes(term))) {
        return <Bean className="w-4 h-4" />;
    }
    if (['fertilizer', 'nutrient', 'package', 'input'].some(term => lowerKey.includes(term))) {
        return <Package className="w-4 h-4" />;
    }
    if (['rotation', 'rotate', 'cycle', 'sequence'].some(term => lowerKey.includes(term))) {
        return <RotateCcw className="w-4 h-4" />;
    }
    return <Package className="w-4 h-4" />;
}

const colors = Array.from({ length: 24 }, (_, i) => {
    const hue = i * 15;
    return [
        hsvToRgb(hue, 0.6, 0.7),
        hsvToRgb(hue, 0.8, 0.9),
        hsvToRgb(hue, 0.4, 0.5),
    ].flat();
}).flat();

function getColorForCategory(category: string): string {
    // Using djb2 hash function which has better distribution
    const hash = category.split('').reduce((acc, char) => {
        return ((acc << 5) + acc) + char.charCodeAt(0);
    }, 5381);

    return colors[Math.abs(hash) % colors.length];
}

function calculatePiechartData(charts?: AlternativeChart[]): ChartData[] {
    if (!charts) {
        return [];
    }

    const OTHER_THRESHOLD = 3;

    return charts.map(chart => {
        const chartTotal = Object.values(chart.values).reduce((total: number, value: number) => total + value, 0);
        const allValues = Object.entries(chart.values).map(([key, value]) => ({
            name: camelCaseToTitle(key),
            key: key,
            value: (value / chartTotal) * 100,
        })).sort((a, b) => b.value - a.value);

        const significantValues = allValues.filter(entry => entry.value >= OTHER_THRESHOLD);

        const otherTotalPercentage = allValues
            .filter(entry => entry.value < OTHER_THRESHOLD)
            .reduce((total, entry) => total + entry.value, 0);
        const otherDataEntry = {
            name: "Other",
            key: "other",
            value: otherTotalPercentage,
        };

        return {
            name: camelCaseToTitle(chart.name),
            key: chart.name,
            total: chartTotal,
            values: otherTotalPercentage > 0
                ? [...significantValues, otherDataEntry]
                : significantValues,
        };
    });
}

function calculateLegendData(alternativeData?: ChartData[], statusQuoData?: ChartData[]){
    if (!alternativeData || !statusQuoData) {
        return [];
    }

    return alternativeData.map((alternativeChart, i) => {
        const statusQuoChart = statusQuoData[i];
        const seen = new Set(alternativeChart.values.map(v => v.key));
        const extraValues = (statusQuoChart?.values ?? []).filter(v => !seen.has(v.key));
        return {
            ...alternativeChart,
            values: [...alternativeChart.values, ...extraValues],
        };
    });
}

type ChartData = {
    name: string;
    key: string;
    total: number;
    values: {
        name: string;
        key: string;
        value: number;
    }[];
}

const emptyChartData: ChartData = {
    name: "",
    key: "",
    total: 0,
    values: [{
        name: "No data",
        key: "no-data",
        value: 1,
    }],
};
const emptyChartColor = "#8884d8";

interface CropPieChartCardProps {
    alternative: Alternative;
    statusQuo?: Alternative;
}

export default function PieChartCard({ alternative, statusQuo }: CropPieChartCardProps) {
    const t = useTranslations("Alternative");
    const [selectedChartIndex, setSelectedChartIndex] = useState(0);
    const alternativeData = useMemo(() => calculatePiechartData(alternative.charts), [alternative.charts]);
    const statusQuoData = useMemo(() => calculatePiechartData(statusQuo?.charts), [statusQuo?.charts]);
    const legendData = useMemo(() => calculateLegendData(alternativeData, statusQuoData), [alternativeData, statusQuoData]);


    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
        >
            <Card className="min-w-0 w-full h-fit">
                <CardHeader className="flex flex-row items-center justify-between pb-2 gap-6">
                    <div className="flex items-center space-x-2">
                        <LucidePieChart className="h-6 w-6 text-primary" />
                        <CardTitle className="text-xl font-bold">{t("charts")}</CardTitle>
                    </div>
                    {alternativeData?.[selectedChartIndex]?.values?.length > 0 && (
                    <DropdownMenu>
                        <DropdownMenuTrigger className="flex h-9 w-[230px] items-center justify-between rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm ring-offset-background focus:outline-none focus:ring-1 focus:ring-ring">
                            {<div className="flex items-center gap-1">
                                {getChartIcon(alternativeData?.[selectedChartIndex]?.key)}
                                {t("diagramName." + alternativeData?.[selectedChartIndex]?.key)}
                            </div>}
                            <ChevronDown className="h-4 w-4 opacity-50" />
                        </DropdownMenuTrigger>
                        <DropdownMenuContent className="w-[180px]">
                            {alternativeData.map((chart, index) => (
                                <DropdownMenuItem
                                    key={index}
                                    onClick={() => setSelectedChartIndex(index)}
                                >
                                    {<div className="flex items-center gap-1">
                                        {getChartIcon(alternativeData[index].key)}
                                        {t("diagramName." + alternativeData?.[index]?.key)}
                                    </div>}
                                </DropdownMenuItem>
                            ))}
                        </DropdownMenuContent>
                        </DropdownMenu>
                    )}
                </CardHeader>
                <CardContent>
                    {alternativeData?.[selectedChartIndex]?.values?.length > 0 ? (
                    <div className="flex flex-col gap-6">
                        <CropPieCharts selectedChartIndex={selectedChartIndex} alternativeData={alternativeData} statusQuoData={statusQuoData} legendData={legendData} />
                    </div>
                    ) : (
                        <div className="flex justify-center items-center h-full">
                            <p className="text-sm text-gray-500">{t("noChartData")}</p>
                        </div>
                    )}
                </CardContent>
            </Card>
        </motion.div >
    )
}

interface CropPieChartsProps {
    selectedChartIndex: number;
    alternativeData: ChartData[];
    statusQuoData: ChartData[];
    legendData: ChartData[];
}

function CropPieCharts({ selectedChartIndex, alternativeData, statusQuoData, legendData }: CropPieChartsProps) {
    const t = useTranslations("Alternative");
    const [activeValueKey, setActiveValueKey] = useState<string>("");
    const legendScrollRef = useRef<HTMLDivElement>(null);

    const scrollLegendToKey = (key: string) => {
        const legendScrollRoot = legendScrollRef.current;
        if (!legendScrollRoot) return;
        const row = legendScrollRoot.querySelector(`[data-legend-key="${CSS.escape(key)}"]`);
        row?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    };

    const activateKey = (key: string) => {
        setActiveValueKey(key);
        scrollLegendToKey(key);
    };

    const resolveActiveKey = (chartData: ChartData[]) => {
        if (activeValueKey === "") return "";
        const values = chartData?.[selectedChartIndex]?.values ?? [];
        const exists = values.some(v => v.key === activeValueKey);
        return exists ? activeValueKey : "other";
    };

    const onPieEnter = (data: { key: string }) => {
        activateKey(data.key);
    };

    const onPieLeave = () => {
        setActiveValueKey("");
    };

    const legendContent = (
        <div className="flex flex-col h-full">
                <div className="flex flex-col gap-2 p-2">
                    {legendData?.[selectedChartIndex]?.values?.map((entry) => {
                        const color = getColorForCategory(entry.key);
                        return (
                            <div
                                key={entry.key}
                                data-legend-key={entry.key}
                                className="flex items-center gap-2 cursor-pointer"
                                onMouseEnter={() => activateKey(entry.key)}
                                onMouseLeave={onPieLeave}
                                style={{ opacity: activeValueKey === "" || activeValueKey === entry.key ? 1 : 0.5 }}
                            >
                                <div
                                    className="flex items-center justify-center min-w-7 min-h-7 rounded-full"
                                    style={{ backgroundColor: color + "50" }}
                                >
                                    <div style={{ color: color }}>
                                        {getChartIcon(entry.key)}
                                    </div>
                                </div>
                                <span>{entry.name}</span>
                            </div>
                        );
                    })}
                </div>
            <div className="flex items-center gap-2 border-t pt-2">
                <span>Total:</span>
                <span>{alternativeData?.[selectedChartIndex]?.total.toLocaleString("da-DK", { maximumFractionDigits: 2 })}</span>
            </div>
        </div>
    );

    const RADIAN = Math.PI / 180;
    const createLabelRenderer = (chartData: ChartData[]) => function PieLabel(props: PieLabelRenderProps) {
        if (!props.percent || !props.cx || !props.cy || !props.midAngle || !props.outerRadius || props.index === undefined) {
            return null;
        }
        const centerX = Number(props.cx);
        const centerY = Number(props.cy);
        const percentage = props.percent * 100;
        const midAngleNum = Number(props.midAngle);
        const outerRadiusNum = Number(props.outerRadius);

        const entryKey = chartData?.[selectedChartIndex]?.values?.[props.index]?.key ?? "";
        const resolved = resolveActiveKey(chartData);

        if (resolved.length > 0 && resolved !== entryKey) {
            return null;
        }

        const radius = outerRadiusNum + 30;
        const x = centerX + radius * Math.cos(-midAngleNum * RADIAN);
        const y = centerY + radius * Math.sin(-midAngleNum * RADIAN);

        const labelLineEndX = centerX + outerRadiusNum * Math.cos(-midAngleNum * RADIAN);
        const labelLineEndY = centerY + outerRadiusNum * Math.sin(-midAngleNum * RADIAN);

        const sliceColor = getColorForCategory(entryKey);

        return (
            <g>
                <line
                    x1={labelLineEndX}
                    y1={labelLineEndY}
                    x2={x}
                    y2={y}
                    stroke={sliceColor}
                    strokeWidth={1}
                />
                <text
                    x={x}
                    y={y}
                    fill={sliceColor}
                    textAnchor={x > centerX ? 'start' : 'end'}
                    dominantBaseline="central"
                    fontSize={14}
                >
                    {`${percentage.toFixed(2)}%`}
                </text>
            </g>
        );
    };

    return (
        <div className="flex flex-col min-h-0 w-full">
            <div className="flex gap-2 items-center">
                <div className="grid grid-cols-[auto_1fr] grid-rows-[auto_auto] relative">
                    <div className="w-fit p-6 col-start-1 row-start-1">
                    <h3 className="text-lg font-semibold text-muted-foreground">{t("alternative")}</h3>
                        <PieChart width={300} height={300}>
                            <Pie
                                dataKey="value"
                                data={alternativeData?.[selectedChartIndex]?.values ?? emptyChartData.values}
                                nameKey="name"
                                cx="50%"
                                cy="50%"
                                startAngle={90}
                                endAngle={-270}
                                outerRadius={75}
                                fill={emptyChartColor}
                                label={createLabelRenderer(alternativeData)}
                                labelLine={false}
                                animationBegin={0}
                                animationDuration={300}
                                onMouseEnter={onPieEnter}
                                onMouseLeave={onPieLeave}
                            >
                                {alternativeData?.[selectedChartIndex]?.values?.map((entry) => {
                                    const resolved = resolveActiveKey(alternativeData);
                                    return (
                                        <Cell
                                            key={`cell-${entry.key}`}
                                            fill={getColorForCategory(entry.key)}
                                            opacity={resolved === "" || resolved === entry.key ? 1 : 0.5}
                                        />
                                    );
                                })}
                            </Pie>
                        </PieChart>
                        <Separator />
                    </div>
                    <div className="w-fit p-6 col-start-1 row-start-2">
                        <h3 className="text-lg font-semibold text-muted-foreground">{t("statusquo")}</h3>
                        <PieChart width={300} height={300}>
                            <Pie
                                dataKey="value"
                                data={statusQuoData?.[selectedChartIndex]?.values ?? emptyChartData.values}
                                nameKey="name"
                                cx="50%"
                                cy="50%"
                                startAngle={90}
                                endAngle={-270}
                                outerRadius={75}
                                fill={emptyChartColor}
                                label={createLabelRenderer(statusQuoData)}
                                labelLine={false}
                                animationBegin={0}
                                animationDuration={300}
                                onMouseEnter={onPieEnter}
                                onMouseLeave={onPieLeave}
                            >
                                {statusQuoData?.[selectedChartIndex]?.values?.map((entry) => {
                                    const resolved = resolveActiveKey(statusQuoData);
                                    return (
                                        <Cell
                                            key={`cell-${entry.key}`}
                                            fill={getColorForCategory(entry.key)}
                                            opacity={resolved === "" || resolved === entry.key ? 1 : 0.5}
                                        />
                                    );
                                })}
                            </Pie>
                        </PieChart>
                    </div>
                    <div
                        ref={legendScrollRef}
                        className="col-start-2 row-start-1 row-span-2 self-center max-h-[600px] overflow-auto"
                    >
                        {legendContent}
                    </div>
                </div>
            </div>
        </div>
    )
}