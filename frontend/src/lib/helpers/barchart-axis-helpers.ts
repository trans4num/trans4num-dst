import { type AlternativeBarChart } from "@/models/alternative";

const Y_AXIS_NUMBER_OF_TICKS = 10;

export function valueRangeForChartData(
  chartData: AlternativeBarChart["chartData"] | undefined,
): [number, number] {
  const values = chartData?.flatMap((category) => Object.values(category.values ?? {})) ?? [];
  if (values.length === 0) return [0, 1];
  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) {
    const delta = min === 0 ? 1 : Math.abs(min) * 0.1;
    return [min - delta, max + delta];
  }
  const pad = (max - min) * 0.05;
  return [min - pad, max + pad];
}

function niceAxisStep(roughStep: number): number {
  const magnitude = 10 ** Math.floor(Math.log10(roughStep));
  const unit = roughStep / magnitude;
  const roundedUnit = unit <= 1 ? 1 : unit <= 2 ? 2 : unit <= 5 ? 5 : 10;
  return roundedUnit * magnitude;
}

export function ticksForValueRange(
  [rangeMin, rangeMax]: [number, number],
  tickSlots = Y_AXIS_NUMBER_OF_TICKS,
): number[] {
  if (!Number.isFinite(rangeMin) || !Number.isFinite(rangeMax)) {
    return [0, 0.25, 0.5, 0.75, 1];
  }
  if (rangeMin === rangeMax) {
    const spread = rangeMin === 0 ? 1 : Math.abs(rangeMin) * 0.1;
    return ticksForValueRange([rangeMin - spread, rangeMax + spread], tickSlots);
  }

  const step = niceAxisStep((rangeMax - rangeMin) / Math.max(1, tickSlots - 1));
  const firstTick = Math.floor(rangeMin / step) * step;
  const lastTick = Math.ceil(rangeMax / step) * step;
  const ticks: number[] = [];
  for (let v = firstTick; v <= lastTick + step * 1e-9; v += step) {
    ticks.push(v);
  }
  return ticks.length >= 2
    ? ticks
    : [rangeMin, (rangeMin + rangeMax) / 2, rangeMax];
}
