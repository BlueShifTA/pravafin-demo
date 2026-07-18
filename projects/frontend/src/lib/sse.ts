// Shared Server-Sent-Events reader for the streaming chat endpoints. Orval
// generates JSON clients only, so the text/event-stream POSTs (copilot chat,
// portfolio-draft chat) are consumed with this hand-rolled reader by design.

export type StreamEvent = { event: string; data: Record<string, unknown> };

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
