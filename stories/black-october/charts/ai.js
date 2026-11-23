import { monthlyBars } from "./bars.js";

export default function draw(ctx) {
  return monthlyBars(ctx, {
    key: "ai_credited", label: "CVEs crediting an AI system or AI lab",
    from: "2025-01-01", highlight: "2026-08-01",
    extra: { key: "cves", label: "All CVEs published" },
  });
}
