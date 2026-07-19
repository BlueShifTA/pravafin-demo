import { Box } from "@mui/material";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// Renders LLM output (the local model answers in markdown) as styled HTML sized
// to MUI body2. react-markdown does not emit raw HTML, so this is XSS-safe.
export function Markdown({ children }: { children: string }) {
  return (
    <Box
      sx={{
        fontSize: "0.875rem",
        lineHeight: 1.5,
        wordBreak: "break-word",
        "& > :first-of-type": { mt: 0 },
        "& > :last-child": { mb: 0 },
        "& p": { my: 1 },
        "& ul, & ol": { my: 1, pl: 2.5 },
        "& li": { mb: 0.25 },
        "& h1, & h2, & h3, & h4, & h5, & h6": {
          fontSize: "0.9rem",
          fontWeight: 700,
          my: 1,
        },
        "& code": {
          fontFamily: "monospace",
          fontSize: "0.85em",
          bgcolor: "action.hover",
          px: 0.5,
          borderRadius: 0.5,
        },
        "& pre": {
          my: 1,
          p: 1,
          bgcolor: "action.hover",
          borderRadius: 1,
          overflowX: "auto",
        },
        "& pre code": { bgcolor: "transparent", px: 0 },
        "& a": { color: "primary.main" },
        "& blockquote": {
          my: 1,
          ml: 0,
          pl: 1.5,
          borderLeft: "3px solid",
          borderColor: "divider",
          color: "text.secondary",
        },
        "& table": { borderCollapse: "collapse", my: 1, width: "100%" },
        "& th, & td": {
          border: "1px solid",
          borderColor: "divider",
          px: 1,
          py: 0.5,
          textAlign: "left",
        },
      }}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </Box>
  );
}
