import type { Metadata } from "next";
import { AppNav } from "@/components/layout/AppNav";
import { AppProviders } from "@/components/layout/AppProviders";
import { PortfolioProvider } from "@/lib/portfolio-context";
import "./globals.css";

export const metadata: Metadata = {
  title: "CoreSat",
  description: "A modern project template with Next.js and FastAPI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AppProviders>
          <PortfolioProvider>
            <AppNav>{children}</AppNav>
          </PortfolioProvider>
        </AppProviders>
      </body>
    </html>
  );
}
