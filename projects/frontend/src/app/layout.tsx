import type { Metadata } from "next";
import { Poppins } from "next/font/google";
import { AppNav } from "@/components/layout/AppNav";
import { AppProviders } from "@/components/layout/AppProviders";
import { PortfolioProvider } from "@/lib/portfolio-context";
import "./globals.css";

const poppins = Poppins({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "CoreSat",
  description: "Core-Satellite portfolio manager with a grounded AI copilot.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={poppins.className}>
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
