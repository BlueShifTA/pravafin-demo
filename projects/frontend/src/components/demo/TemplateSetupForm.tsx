"use client";

import { MenuItem, Stack, Typography } from "@mui/material";
import { useState } from "react";

import { Section } from "@/components/layout/Section";
import { AppButton } from "@/components/ui/buttons/AppButton";
import { ButtonRow } from "@/components/ui/buttons/ButtonRow";
import { ButtonWithSpinner } from "@/components/ui/buttons/ButtonWithSpinner";
import { AppTextField } from "@/components/ui/fields/AppTextField";

export function TemplateSetupForm() {
  const [templateName, setTemplateName] = useState("my-service");
  const [environment, setEnvironment] = useState("local");
  const [note, setNote] = useState("Placeholder values only. Replace with your product fields.");
  const [statusText, setStatusText] = useState("Ready");
  const [isChecking, setIsChecking] = useState(false);

  async function handleDryCheck() {
    setIsChecking(true);
    setStatusText("Running placeholder dry-check...");

    try {
      await new Promise((resolve) => {
        window.setTimeout(resolve, 700);
      });
      setStatusText(`Dry-check passed for "${templateName}" (${environment}).`);
    } finally {
      setIsChecking(false);
    }
  }

  function handleReset() {
    setTemplateName("my-service");
    setEnvironment("local");
    setNote("Placeholder values only. Replace with your product fields.");
    setStatusText("Reset to placeholder defaults.");
  }

  function handleSavePlaceholder() {
    setStatusText("Saved placeholder configuration locally (demo only).");
  }

  return (
    <Section
      title="Reusable Controls Demo"
      description="This section demonstrates modular buttons and text fields that can be reused across template pages and feature modules."
    >
      <Stack spacing={2}>
        <div className="grid gap-3 md:grid-cols-2">
          <AppTextField
            label="Template Name"
            value={templateName}
            onChange={(event) => setTemplateName(event.target.value)}
            helperText="Generic placeholder field for a future feature module."
          />
          <AppTextField
            select
            label="Target Environment"
            value={environment}
            onChange={(event) => setEnvironment(event.target.value)}
            helperText="Use placeholders in template demos; map to real environments later."
          >
            <MenuItem value="local">local</MenuItem>
            <MenuItem value="staging">staging</MenuItem>
            <MenuItem value="production">production</MenuItem>
          </AppTextField>
        </div>

        <AppTextField
          label="Setup Note"
          multiline
          minRows={3}
          value={note}
          onChange={(event) => setNote(event.target.value)}
        />

        <ButtonRow>
          <ButtonWithSpinner isLoading={isChecking} onClick={handleDryCheck}>
            Run Dry Check
          </ButtonWithSpinner>
          <AppButton variant="outlined" onClick={handleSavePlaceholder}>
            Save Placeholder Config
          </AppButton>
          <AppButton color="inherit" variant="text" onClick={handleReset}>
            Reset
          </AppButton>
        </ButtonRow>

        <Typography variant="body2" color="text.secondary">
          {statusText}
        </Typography>
      </Stack>
    </Section>
  );
}
