"use client";

import {
  Card,
  CardContent,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import { PageShell } from "@/components/layout/PageShell";
import {
  useListQuarantineApiIngestQuarantineGet,
  useListRunsApiIngestRunsGet,
} from "@/lib/generated/endpoints";

function statusColor(status: string): "success" | "error" | "default" {
  if (status === "succeeded") return "success";
  if (status === "failed") return "error";
  return "default";
}

export default function IngestionPage() {
  const runsQuery = useListRunsApiIngestRunsGet();
  const runs = runsQuery.data?.status === 200 ? runsQuery.data.data : [];
  const quarantineQuery = useListQuarantineApiIngestQuarantineGet();
  const quarantine = quarantineQuery.data?.status === 200 ? quarantineQuery.data.data : [];

  return (
    <PageShell
      title="Ingestion"
      description="Every run is checksummed (idempotent); invalid rows land in quarantine with a reason — never silently in fact tables."
    >
      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
            Runs
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Source</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">In</TableCell>
                <TableCell align="right">OK</TableCell>
                <TableCell align="right">Quarantined</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {runs.slice(0, 30).map((run) => (
                <TableRow key={String(run.id)}>
                  <TableCell>{String(run.id)}</TableCell>
                  <TableCell>{String(run.source)}</TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      label={String(run.status)}
                      color={statusColor(String(run.status))}
                    />
                  </TableCell>
                  <TableCell align="right">{String(run.rows_in)}</TableCell>
                  <TableCell align="right">{String(run.rows_ok)}</TableCell>
                  <TableCell align="right">{String(run.rows_quarantined)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
            Quarantine
          </Typography>
          {quarantine.length === 0 && (
            <Typography color="text.secondary">Empty — all rows passed their contracts.</Typography>
          )}
          <Table size="small">
            <TableBody>
              {quarantine.map((row) => (
                <TableRow key={String(row.id)}>
                  <TableCell>{String(row.source)}</TableCell>
                  <TableCell sx={{ color: "error.main" }}>{String(row.reason)}</TableCell>
                  <TableCell sx={{ fontFamily: "monospace", fontSize: 12 }}>
                    {JSON.stringify(row.payload).slice(0, 120)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </PageShell>
  );
}
