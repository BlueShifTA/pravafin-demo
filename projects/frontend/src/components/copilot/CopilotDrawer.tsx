"use client";

import {
  Box,
  Chip,
  Divider,
  Drawer,
  IconButton,
  LinearProgress,
  Tooltip,
  Typography,
} from "@mui/material";
import DeleteSweepIcon from "@mui/icons-material/DeleteSweep";
import SendIcon from "@mui/icons-material/Send";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  getChatHistoryApiPortfoliosPortfolioIdChatGetQueryKey,
  useChatHistoryApiPortfoliosPortfolioIdChatGet,
  useClearChatApiPortfoliosPortfolioIdChatDelete,
  useCopilotInfoApiCopilotInfoGet,
} from "@/lib/generated/endpoints";
import type { ChatMessageOut } from "@/lib/generated/models";
import { usePortfolio } from "@/lib/portfolio-context";
import { AGENT_TIMEOUT_MS, agentStageLabel, readSseEvents } from "@/lib/sse";
import { AppTextField } from "@/components/ui/fields/AppTextField";

const DRAWER_WIDTH = { xs: "85vw", sm: 380 };

function MessageBubble({ message }: { message: ChatMessageOut }) {
  const isUser = message.role === "user";
  return (
    <Box sx={{ alignSelf: isUser ? "flex-end" : "flex-start", maxWidth: "90%" }}>
      <Box
        sx={{
          px: 1.5,
          py: 1,
          borderRadius: 2,
          bgcolor: isUser ? "primary.main" : "action.hover",
          color: isUser ? "primary.contrastText" : "text.primary",
        }}
      >
        <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
          {message.content}
        </Typography>
      </Box>
      {message.citations.length > 0 && (
        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, mt: 0.5 }}>
          {message.citations.map((citation) => (
            <Tooltip
              key={citation.id}
              title={<Box sx={{ whiteSpace: "pre-wrap" }}>{citation.content}</Box>}
            >
              <Chip label={citation.id} size="small" variant="outlined" />
            </Tooltip>
          ))}
        </Box>
      )}
    </Box>
  );
}

export function CopilotDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { portfolioId } = usePortfolio();
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [phase, setPhase] = useState<string | null>(null);
  const [pendingUser, setPendingUser] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const historyQuery = useChatHistoryApiPortfoliosPortfolioIdChatGet(portfolioId ?? 0, {
    query: { enabled: open && portfolioId != null },
  });
  const history = historyQuery.data?.status === 200 ? historyQuery.data.data : [];
  const infoQuery = useCopilotInfoApiCopilotInfoGet({ query: { enabled: open } });
  const modelName = infoQuery.data?.status === 200 ? infoQuery.data.data.model : "…";
  const clearChat = useClearChatApiPortfoliosPortfolioIdChatDelete({
    mutation: {
      onSuccess: () => {
        if (portfolioId == null) return;
        void queryClient.invalidateQueries({
          queryKey: getChatHistoryApiPortfoliosPortfolioIdChatGetQueryKey(portfolioId),
        });
      },
    },
  });

  async function send() {
    const message = draft.trim();
    if (!message || sending || portfolioId == null) return;
    setDraft("");
    setError(null);
    setSending(true);
    setPendingUser(message);
    setPhase("Routing…");
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), AGENT_TIMEOUT_MS);
    try {
      const response = await fetch(`/api/portfolios/${portfolioId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
        signal: controller.signal,
      });
      if (!response.ok || response.body == null) {
        setError(`Chat failed (${response.status}).`);
        return;
      }
      for await (const { event, data } of readSseEvents(response.body)) {
        const stage = agentStageLabel(event, data);
        if (stage != null) setPhase(stage);
        if (event === "error") setError(String(data.message ?? "The copilot failed."));
      }
      await queryClient.invalidateQueries({
        queryKey: getChatHistoryApiPortfoliosPortfolioIdChatGetQueryKey(portfolioId),
      });
    } catch {
      setError(
        controller.signal.aborted
          ? "The copilot timed out after 5 minutes."
          : "Chat failed — is the backend running?"
      );
    } finally {
      clearTimeout(timer);
      setSending(false);
      setPhase(null);
      setPendingUser(null);
    }
  }

  return (
    <Drawer anchor="right" open={open} onClose={onClose}>
      <Box
        sx={{
          width: DRAWER_WIDTH,
          display: "flex",
          flexDirection: "column",
          height: "100%",
          pt: 8,
        }}
      >
        <Box
          sx={{
            px: 2,
            py: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Copilot
          </Typography>
          <Tooltip title="Clear chat context">
            <span>
              <IconButton
                aria-label="clear chat"
                size="small"
                onClick={() => {
                  if (portfolioId != null) clearChat.mutate({ portfolioId });
                }}
                disabled={portfolioId == null || sending || history.length === 0}
              >
                <DeleteSweepIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
        <Divider />
        {/* column-reverse pins the view to the newest message natively — no
            scroll effects; DOM order is therefore newest-first */}
        <Box
          sx={{
            flexGrow: 1,
            overflowY: "auto",
            px: 2,
            py: 1.5,
            display: "flex",
            flexDirection: "column-reverse",
            gap: 1.5,
          }}
        >
          {portfolioId == null ? (
            <Typography color="text.secondary">Select a portfolio to start chatting.</Typography>
          ) : (
            <>
              {error != null && (
                <Typography variant="body2" color="error">
                  {error}
                </Typography>
              )}
              {sending && (
                <Box sx={{ alignSelf: "flex-start", maxWidth: "90%" }}>
                  <Box
                    aria-label="agent is typing"
                    sx={{
                      px: 1.5,
                      py: 1.25,
                      borderRadius: 2,
                      bgcolor: "action.hover",
                      display: "inline-flex",
                      gap: 0.5,
                      "@keyframes copilotPulse": {
                        "0%, 80%, 100%": { opacity: 0.25 },
                        "40%": { opacity: 1 },
                      },
                      "& > span": {
                        width: 6,
                        height: 6,
                        borderRadius: "50%",
                        bgcolor: "text.secondary",
                        animation: "copilotPulse 1.2s infinite ease-in-out",
                      },
                      "& > span:nth-of-type(2)": { animationDelay: "0.2s" },
                      "& > span:nth-of-type(3)": { animationDelay: "0.4s" },
                    }}
                  >
                    <span />
                    <span />
                    <span />
                  </Box>
                  {phase != null && (
                    <>
                      <Typography variant="caption" color="text.secondary">
                        {phase}
                      </Typography>
                      <LinearProgress sx={{ mt: 0.5 }} />
                    </>
                  )}
                </Box>
              )}
              {pendingUser != null && (
                <Box sx={{ alignSelf: "flex-end", maxWidth: "90%" }}>
                  <Box
                    sx={{
                      px: 1.5,
                      py: 1,
                      borderRadius: 2,
                      bgcolor: "primary.main",
                      color: "primary.contrastText",
                    }}
                  >
                    <Typography variant="body2">{pendingUser}</Typography>
                  </Box>
                </Box>
              )}
              {[...history].reverse().map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
            </>
          )}
        </Box>
        <Divider />
        <Box sx={{ display: "flex", gap: 1, p: 1.5, alignItems: "center" }}>
          <AppTextField
            multiline
            maxRows={4}
            placeholder="Ask about this portfolio…"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void send();
              }
            }}
            disabled={portfolioId == null || sending}
            slotProps={{ htmlInput: { "aria-label": "chat message" } }}
          />
          <IconButton
            aria-label="send message"
            color="primary"
            onClick={() => void send()}
            disabled={portfolioId == null || sending || draft.trim() === ""}
          >
            <SendIcon />
          </IconButton>
        </Box>
        <Box sx={{ px: 2, pb: 1.5 }}>
          <Typography variant="caption" color="text.secondary">
            Model: {modelName}
          </Typography>
        </Box>
      </Box>
    </Drawer>
  );
}
