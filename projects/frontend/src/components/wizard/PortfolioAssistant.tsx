"use client";

import { Alert, Box, Button, Chip, LinearProgress, Paper, Typography } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import { useState } from "react";

import type { ChatTurn, PortfolioDraft } from "@/lib/generated/models";
import { formatMoney, formatPercent } from "@/lib/format";
import { AGENT_TIMEOUT_MS, agentStageLabel, readSseEvents } from "@/lib/sse";
import { AppTextField } from "@/components/ui/fields/AppTextField";

const CONFIRM_MESSAGE = "Yes, build this portfolio.";

function DraftCard({ draft }: { draft: PortfolioDraft }) {
  return (
    <Paper variant="outlined" sx={{ p: 2, alignSelf: "flex-start", maxWidth: "95%" }}>
      <Typography sx={{ fontWeight: 600, mb: 1 }}>{draft.name}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
        {formatMoney(draft.initial_capital)} + {formatMoney(draft.monthly_contribution)}/month
      </Typography>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
        <Chip label={draft.core_fund_ticker} size="small" color="primary" />
        <Typography variant="body2">core · {formatPercent(draft.core_weight, 0)}</Typography>
      </Box>
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mt: 1 }}>
        {draft.satellites.map((position) => (
          <Chip
            key={position.ticker}
            label={`${position.ticker} · ${formatPercent(position.weight, 0)}`}
            size="small"
            variant="outlined"
          />
        ))}
      </Box>
    </Paper>
  );
}

export function PortfolioAssistant({ onCreated }: { onCreated: (portfolioId: number) => void }) {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [draft, setDraft] = useState<PortfolioDraft | null>(null);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [stage, setStage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function send(message: string, confirm = false) {
    if (!message.trim() || sending) return;
    setError(null);
    setSending(true);
    setStage("Routing…");
    const history = turns;
    setTurns([...history, { role: "user", content: message }]);
    setInput("");
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), AGENT_TIMEOUT_MS);
    try {
      const response = await fetch("/api/portfolio-draft/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history, proposed_draft: draft, confirm }),
        signal: controller.signal,
      });
      if (!response.ok || response.body == null) {
        setError(`Assistant failed (${response.status}).`);
        return;
      }
      for await (const { event, data } of readSseEvents(response.body)) {
        const nextStage = agentStageLabel(event, data);
        if (nextStage != null) setStage(nextStage);
        if (event === "answer") {
          const text = typeof data.text === "string" ? data.text : "";
          setTurns((prev) => [...prev, { role: "assistant", content: text }]);
          if (data.action === "propose" && data.draft) {
            setDraft(data.draft as PortfolioDraft);
          }
        } else if (event === "created") {
          onCreated(Number(data.portfolio_id));
          return;
        } else if (event === "error") {
          setError(String(data.message ?? "The assistant failed."));
        }
      }
    } catch {
      setError(
        controller.signal.aborted
          ? "The assistant timed out after 5 minutes."
          : "Assistant failed — is the backend running?"
      );
    } finally {
      clearTimeout(timer);
      setSending(false);
      setStage(null);
    }
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "60vh", maxWidth: 720 }}>
      <Box
        sx={{
          flexGrow: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 1.5,
          p: 1,
        }}
      >
        {turns.length === 0 && (
          <Typography color="text.secondary">
            Describe the portfolio you want — for example: &ldquo;60% core ETF in tech and medical,
            40% split across five high-upside stocks from different sectors.&rdquo;
          </Typography>
        )}
        {turns.map((turn, index) => (
          <Box
            key={index}
            sx={{
              alignSelf: turn.role === "user" ? "flex-end" : "flex-start",
              maxWidth: "90%",
              px: 1.5,
              py: 1,
              borderRadius: 2,
              bgcolor: turn.role === "user" ? "primary.main" : "action.hover",
              color: turn.role === "user" ? "primary.contrastText" : "text.primary",
            }}
          >
            <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
              {turn.content}
            </Typography>
          </Box>
        ))}
        {draft != null && <DraftCard draft={draft} />}
        {draft != null && !sending && (
          <Button
            variant="contained"
            sx={{ alignSelf: "flex-start" }}
            onClick={() => void send(CONFIRM_MESSAGE, true)}
          >
            Looks good — build it
          </Button>
        )}
        {sending && (
          <Box sx={{ alignSelf: "flex-start", minWidth: 200 }}>
            {stage != null && (
              <Typography variant="caption" color="text.secondary">
                {stage}
              </Typography>
            )}
            <LinearProgress sx={{ mt: 0.5 }} />
          </Box>
        )}
        {error != null && <Alert severity="error">{error}</Alert>}
      </Box>
      <Box sx={{ display: "flex", gap: 1, alignItems: "center", pt: 1 }}>
        <AppTextField
          multiline
          maxRows={3}
          placeholder="Describe the portfolio you want…"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void send(input);
            }
          }}
          disabled={sending}
        />
        <Button
          aria-label="send message"
          variant="contained"
          onClick={() => void send(input)}
          disabled={sending || input.trim() === ""}
          sx={{ minWidth: 0, px: 2 }}
        >
          <SendIcon />
        </Button>
      </Box>
    </Box>
  );
}
