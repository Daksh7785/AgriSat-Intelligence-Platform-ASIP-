/**
 * Provenance Badge — shown next to any accuracy metric (overall accuracy, Kappa,
 * F1 score) sourced from a model_run that used synthetic ground truth.
 *
 * This component must be rendered everywhere an accuracy number is shown in the
 * dashboard (DashboardPage.tsx model-performance cards, the validation report view).
 * It is intentionally visually distinct (amber, not red — this is a disclosed
 * limitation, not an error state) so it cannot be missed without being alarmist.
 */
import { AlertTriangle, CheckCircle2 } from "lucide-react";

interface ProvenanceBadgeProps {
  isSynthetic: boolean;
  syntheticFraction: number;   // 0.0 - 1.0
  nSamples: number;
}

export function ProvenanceBadge({ isSynthetic, syntheticFraction, nSamples }: ProvenanceBadgeProps) {
  if (!isSynthetic) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-green-50 px-2.5 py-1 text-xs font-medium text-green-800">
        <CheckCircle2 className="h-3.5 w-3.5" />
        Field-verified ground truth ({nSamples} points)
      </span>
    );
  }

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-800"
      title="This accuracy figure was computed against synthetic, not field-verified, ground truth labels. Treat as a pipeline sanity check, not a real-world accuracy claim."
    >
      <AlertTriangle className="h-3.5 w-3.5" />
      {Math.round(syntheticFraction * 100)}% synthetic ground truth — pipeline check only
    </span>
  );
}
