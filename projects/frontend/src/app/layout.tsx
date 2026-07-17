import type { Metadata } from "next";
import { AppProviders } from "@/components/layout/AppProviders";
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
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
