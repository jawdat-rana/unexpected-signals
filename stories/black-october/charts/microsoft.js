import { monthlyBars } from "./bars.js";

export default function draw(ctx) {
  return monthlyBars(ctx, {
    key: "microsoft", label: "Flaws Microsoft published",
    from: "2024-01-01", highlight: "2026-07-01",
    extra: { key: "microsoft_exploited", label: "Already exploited when fixed" },
  });
}
