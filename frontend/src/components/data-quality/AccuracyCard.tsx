/**
 * Accuracy Card — wraps ProvenanceBadge around the actual OA/Kappa numbers, for use
 * in the model performance section of the dashboard. Replaces any bare accuracy
 * number currently rendered without provenance context.
 */
import { ProvenanceBadge } from "./ProvenanceBadge";

interface AccuracyCardProps {
  modelName: string;
  overallAccuracy: number;
  kappa: number;
  isSynthetic: boolean;
  syntheticFraction: number;
  nSamples: number;
}

export function AccuracyCard({
  modelName, overallAccuracy, kappa, isSynthetic, syntheticFraction, nSamples,
}: AccuracyCardProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900">{modelName}</h3>
        <ProvenanceBadge
          isSynthetic={isSynthetic}
          syntheticFraction={syntheticFraction}
          nSamples={nSamples}
        />
      </div>
      <div className="mt-3 grid grid-cols-2 gap-4">
        <div>
          <p className="text-2xl font-semibold text-gray-900">{(overallAccuracy * 100).toFixed(1)}%</p>
          <p className="text-xs text-gray-500">Overall accuracy</p>
        </div>
        <div>
          <p className="text-2xl font-semibold text-gray-900">{kappa.toFixed(2)}</p>
          <p className="text-xs text-gray-500">Kappa coefficient</p>
        </div>
      </div>
    </div>
  );
}
