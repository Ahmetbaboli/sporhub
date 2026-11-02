"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { tr } from "@/lib/i18n/tr";
import { positionTicks, type SeriesPoint } from "@/lib/series";

const HEIGHT = 220;
const TICK = { fill: "var(--muted-foreground)", fontSize: 11 };
// 8px markers with a 2px surface ring, 2px line (single series: no legend, title names it).
const DOT = { r: 4, fill: "var(--primary)", stroke: "var(--card)", strokeWidth: 2 };
const ACTIVE_DOT = {
  r: 6,
  fill: "var(--primary)",
  stroke: "var(--card)",
  strokeWidth: 2,
};

export type ValueFormat = "int" | "pct" | "position";

export function formatValue(value: number, format: ValueFormat): string {
  if (format === "pct") return `%${value}`;
  if (format === "position") return `${value}.`;
  return String(value);
}

interface TooltipBodyProps {
  active?: boolean;
  payload?: { payload: SeriesPoint }[];
  valueLabel: string;
  format: ValueFormat;
}

function TooltipBody({ active, payload, valueLabel, format }: TooltipBodyProps) {
  const point = active ? payload?.[0]?.payload : undefined;
  if (!point) return null;
  return (
    <div className="bg-card rounded-md border px-3 py-2 text-xs shadow-md">
      <p className="text-muted-foreground">{point.label}</p>
      <p className="num text-foreground mt-0.5 font-semibold">
        {valueLabel}: {formatValue(point.value, format)}
      </p>
    </div>
  );
}

/** One measure over time, one axis. Positions are drawn with 1 at the top. */
export function SeriesChart({
  title,
  description,
  data,
  valueLabel,
  xLabel,
  format = "int",
}: {
  title: string;
  description?: string;
  data: SeriesPoint[];
  valueLabel: string;
  xLabel: string;
  format?: ValueFormat;
}) {
  const reversed = format === "position";
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <figure className="bg-card overflow-hidden rounded-lg border">
      <figcaption className="bg-muted/60 border-b px-3 py-2">
        <span className="font-display text-lg font-semibold tracking-wide uppercase">
          {title}
        </span>
        {description ? (
          <span className="text-muted-foreground block text-xs">{description}</span>
        ) : null}
      </figcaption>
      <div
        className="px-1 pt-3"
        role="img"
        aria-label={`${title}: ${tr.charts.summary(data.length)}`}
      >
        <ResponsiveContainer width="100%" height={HEIGHT}>
          <LineChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--border)" strokeDasharray="0" />
            <XAxis
              dataKey="x"
              tick={TICK}
              tickLine={false}
              axisLine={{ stroke: "var(--border)" }}
              minTickGap={12}
            />
            <YAxis
              width={36}
              tick={TICK}
              tickLine={false}
              axisLine={false}
              allowDecimals={false}
              reversed={reversed}
              ticks={reversed ? positionTicks(max) : undefined}
              interval={reversed ? 0 : "preserveEnd"}
              domain={reversed ? [1, max] : format === "pct" ? [0, 100] : [0, "auto"]}
              tickFormatter={(v: number) => formatValue(v, format)}
            />
            <Tooltip
              cursor={{ stroke: "var(--muted-foreground)", strokeDasharray: "3 3" }}
              content={<TooltipBody valueLabel={valueLabel} format={format} />}
            />
            <Line
              type={reversed ? "linear" : "monotone"}
              dataKey="value"
              stroke="var(--primary)"
              strokeWidth={2}
              dot={data.length <= 40 ? DOT : false}
              activeDot={ACTIVE_DOT}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <details className="border-t px-3 py-2 text-sm">
        <summary className="text-primary cursor-pointer text-xs font-medium">
          {tr.charts.showTable}
        </summary>
        <table className="num mt-2 w-full text-sm">
          <caption className="sr-only">{title}</caption>
          <thead className="text-muted-foreground text-xs">
            <tr>
              <th scope="col" className="py-1 text-left">
                {xLabel}
              </th>
              <th scope="col" className="py-1 text-right">
                {valueLabel}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data.map((point, i) => (
              <tr key={`${point.x}-${i}`}>
                <td className="py-1">{point.label}</td>
                <td className="py-1 text-right font-semibold">
                  {formatValue(point.value, format)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}
