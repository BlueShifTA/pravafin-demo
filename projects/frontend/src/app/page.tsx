import { PageShell } from "@/components/layout/PageShell";
import { Section } from "@/components/layout/Section";
import { BackendHealthSection } from "@/components/demo/BackendHealthSection";
import { TemplateSetupForm } from "@/components/demo/TemplateSetupForm";
export default function Home() {
  return (
    <PageShell
      eyebrow="Template Frontend Foundation"
      title="Modular UI structure with shared buttons and fields"
      description="This starter keeps App Router and Tailwind, then adds a mono-inspired MUI theme layer, shared UI modules, and placeholder-first demo components."
      actions={
        <>
          <a className="template-link-pill" href="http://127.0.0.1:8000/docs">
            API Docs
          </a>
          <code className="template-code-pill">just run-frontend</code>
          <code className="template-code-pill">just generate-frontend-types</code>
        </>
      }
    >
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <BackendHealthSection />
        <Section title="Commands" description="Template-safe aliases and core tasks.">
          <p className="font-mono text-sm">just lint / test / run-ci</p>
          <p className="mt-2 font-mono text-sm">just format / typecheck</p>
        </Section>
        <Section title="Agent Docs" description="Scaffold instructions and coding rules.">
          <p className="font-mono text-sm">CLAUDE.md</p>
          <p className="mt-2 text-sm text-slate-500">
            Add feature-specific rules without leaking product details into the template.
          </p>
        </Section>
        <Section title="Bootstrap" description="Template setup and API client generation.">
          <p className="font-mono text-sm">just bootstrap</p>
          <p className="mt-2 font-mono text-sm">pnpm run api</p>
        </Section>
      </div>

      <TemplateSetupForm />
    </PageShell>
  );
}
