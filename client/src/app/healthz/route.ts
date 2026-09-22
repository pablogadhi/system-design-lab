// Liveness/readiness endpoint for the chart's probes.
export const dynamic = "force-dynamic";

export function GET() {
  return Response.json({ status: "ok" });
}
