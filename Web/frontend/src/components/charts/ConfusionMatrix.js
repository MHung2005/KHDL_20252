"use client";
/**
 * src/components/charts/ConfusionMatrix.js
 */

const CLASS_LABELS = ["Normal", "Hate", "Offensv."];
const CLASS_COLORS = ["#34d399", "#f87171", "#fb923c"];

export default function ConfusionMatrix({ matrix, modelName }) {
  if (!Array.isArray(matrix) || !matrix.length) return null;

  const flat = matrix.flat();
  const maxVal = Math.max(...flat);

  return (
    <div>
      {modelName && (
        <p className="text-center text-[10px] text-ink-muted mb-3">
          Confusion Matrix — <span className="text-ink font-semibold">{modelName}</span>
        </p>
      )}

      {/* Predicted header */}
      <div className="grid gap-1" style={{ gridTemplateColumns: "52px repeat(3, 1fr)" }}>
        <div />
        {CLASS_LABELS.map((l, i) => (
          <div key={l} className="text-center pb-1.5 text-[10px] font-bold" style={{ color: CLASS_COLORS[i] }}>
            {l}
          </div>
        ))}

        {/* Actual rows */}
        {matrix.map((row, ri) => [
          <div
            key={`label-${ri}`}
            className="flex items-center justify-end pr-2 text-[10px] font-bold"
            style={{ color: CLASS_COLORS[ri] }}
          >
            {CLASS_LABELS[ri]}
          </div>,
          ...row.map((val, ci) => {
            const intensity = maxVal > 0 ? val / maxVal : 0;
            const isDiag = ri === ci;
            return (
              <div
                key={`${ri}-${ci}`}
                className="rounded-lg py-2.5 px-1 text-center text-xs font-bold transition-all"
                style={{
                  background: isDiag
                    ? `rgba(56,189,248,${0.12 + intensity * 0.45})`
                    : `rgba(248,113,113,${0.04 + intensity * 0.28})`,
                  border: isDiag
                    ? "1px solid rgba(56,189,248,0.3)"
                    : "1px solid rgba(248,113,113,0.15)",
                  color: isDiag ? "#e0f2fe" : "#fca5a5",
                }}
              >
                {val.toLocaleString("vi-VN")}
              </div>
            );
          }),
        ])}
      </div>

      <div className="mt-3 flex items-center justify-center gap-5 text-[10px] text-ink-muted">
        <span className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded bg-brand-400/40 border border-brand-400/50" />
          Đúng (diagonal)
        </span>
        <span className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded bg-red-400/20 border border-red-400/30" />
          Sai
        </span>
      </div>
    </div>
  );
}
