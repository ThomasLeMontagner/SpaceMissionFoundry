import { useEffect, useState } from "react";
import { request } from "./api";

type Recovery = {
  available: boolean;
  interrupted: boolean;
  requires_confirmation: boolean;
  reason: string;
  revision: number;
  completed: string[];
  stage: string;
};

export default function RecoveryControls({
  missionId,
  runId,
  revision,
  busy,
  act,
}: {
  missionId: string;
  runId: string;
  revision: number;
  busy: boolean;
  act: (path: string, body?: object) => unknown;
}) {
  const [state, setState] = useState<Recovery | null>(null);
  const [error, setError] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const result = await request(
          `/missions/${missionId}/collaboration/${runId}/recovery`,
        );
        if (!cancelled) {
          setState(result);
          setError("");
        }
      } catch {
        if (!cancelled) setError("Recovery status unavailable. Reconnecting…");
      } finally {
        if (!cancelled) timer = setTimeout(poll, 5000);
      }
    }
    void poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [missionId, runId, revision]);

  return (
    <section className="notice" aria-label="Execution recovery">
      <p role="status">
        {error || state?.reason || "Checking saved execution lease…"}
      </p>
      {state?.interrupted && (
        <>
          <p>
            {state.completed.length} completed tasks will be preserved. Recovery
            prepares the unfinished task ({state.stage}); then choose Run next
            task or Run until review to continue. Recovery itself makes no model
            calls.
          </p>
          {state.requires_confirmation && (
            <label>
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(event) => setConfirmed(event.target.checked)}
              />
              I understand the previous model call has an unknown outcome and
              may already have incurred a charge. Retrying may incur another
              charge.
            </label>
          )}
          <button
            disabled={
              busy ||
              !!error ||
              !state.available ||
              state.revision !== revision ||
              (state.requires_confirmation && !confirmed)
            }
            onClick={() =>
              act(`/collaboration/${runId}/recover`, {
                retry_uncertain: confirmed,
              })
            }
          >
            Resume from checkpoint
          </button>
        </>
      )}
    </section>
  );
}
