import { Card, CardContent, Typography } from "@mui/material";

export function StatBox({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: string;
}) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="overline" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="h6" sx={{ fontWeight: 700, color: accent }}>
          {value}
        </Typography>
      </CardContent>
    </Card>
  );
}
