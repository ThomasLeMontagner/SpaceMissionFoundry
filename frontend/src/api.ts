let ownerToken = "";
export function setToken(token: string) {
  ownerToken = token;
}
export async function request(path: string, body?: unknown) {
  const result = await fetch("/api" + path, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      "Content-Type": "application/json",
      ...(ownerToken ? { Authorization: "Bearer " + ownerToken } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!result.ok) {
    const error = await result
      .json()
      .catch(() => ({ detail: "Server unavailable" }));
    throw Error(
      typeof error.detail === "string"
        ? error.detail
        : JSON.stringify(error.detail),
    );
  }
  return result.json();
}
export async function download(path: string, format: string) {
  const res = await fetch("/api" + path, {
    headers: ownerToken ? { Authorization: "Bearer " + ownerToken } : {},
  });
  if (!res.ok) throw Error("Export failed; create a baseline first.");
  const url = URL.createObjectURL(await res.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = "mission-concept." + format;
  a.click();
  URL.revokeObjectURL(url);
}
export function subscribe(id: string, onRevision: () => void) {
  const abort = new AbortController();
  void (async () => {
    while (!abort.signal.aborted) {
      try {
        const res = await fetch(`/api/missions/${id}/events`, {
          signal: abort.signal,
          headers: ownerToken ? { Authorization: "Bearer " + ownerToken } : {},
        });
        if (!res.ok) break;
        const reader = res.body?.getReader();
        if (!reader) break;
        let buffer = "";
        const decoder = new TextDecoder();
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          let split;
          while ((split = buffer.indexOf("\n\n")) >= 0) {
            const msg = buffer.slice(0, split);
            buffer = buffer.slice(split + 2);
            if (msg.includes("event: revision")) onRevision();
          }
        }
      } catch {
        if (abort.signal.aborted) break;
        await new Promise((r) => setTimeout(r, 2000));
      }
    }
  })();
  return () => abort.abort();
}
