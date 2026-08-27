import { Newsreader, IBM_Plex_Mono } from "next/font/google";
import type { Metadata } from "next";

import { TooltipProvider } from "@/components/ui/tooltip";

import "./globals.css";

const serif = Newsreader({
  subsets: ["latin"],
  variable: "--font-serif",
  display: "swap",
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "GPU constructions Run001 never ran",
  description:
    "Explicit Ramsey graph families that are GPU-native but were skipped in RamseyConstructor-GNN Run001: generalized Paley, F2 Cayley, polarity graphs, Singer circulants, and Kronecker lifts.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${serif.variable} ${mono.variable} dark h-full antialiased`}
    >
      <body className="min-h-full bg-[var(--ink)] text-[var(--cream)]">
        <TooltipProvider>{children}</TooltipProvider>
      </body>
    </html>
  );
}
