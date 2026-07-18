// Shared Server-Sent-Events reader for the streaming chat endpoints. Orval
// generates JSON clients only, so the text/event-stream POSTs (copilot chat,
// portfolio-draft chat) are consumed with this hand-rolled reader by design.

export type StreamEvent = { event: string; data: Record<string, unknown> };

// Agent runs on a slow reasoning model; allow up to 5 minutes before aborting.
export const AGENT_TIMEOUT_MS = 5 * 60 * 1000;

// Map a streamed SSE event to a short human label of what the agent is really
// doing, from the real plan/evidence events (no fake steps). Returns null for
// events that carry no progress meaning (answer/created/error).
export function agentStageLabel(event: string, data: Record<string, unknown>): string | null {
  if (event === "plan") {
    const steps = Array.isArray(data.steps) ? (data.steps as Array<Record<string, unknown>>) : [];
    if (steps.length === 0) return "Thinking…";
    const tools = new Set(steps.map((step) => String(step.tool)));
    if (tools.has("run_sql")) return "Querying the database…";
    if (tools.has("rag_search")) return "Searching documents…";
    if (tools.has("get_projection")) return "Running the projection…";
    return "Planning…";
  }
  if (event === "evidence") return "Synthesizing the answer…";
  return null;
}

export async function* readSseEvents(
  body: ReadableStream<Uint8Array>
): AsyncGenerator<StreamEvent> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let separator = buffer.indexOf("\n\n");
    while (separator >= 0) {
      const block = buffer.slice(0, separator);
      buffer = buffer.slice(separator + 2);
      let event = "";
      let data: Record<string, unknown> | null = null;
      for (const line of block.split("\n")) {
        if (line.startsWith("event: ")) event = line.slice(7);
        if (line.startsWith("data: ")) data = JSON.parse(line.slice(6));
      }
      if (event && data) yield { event, data };
      separator = buffer.indexOf("\n\n");
    }
  }
}
