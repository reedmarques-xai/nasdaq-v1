import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Market Signal Generator",
  description: "NASDAQ Data Link + Grok AI trading signals",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased min-h-screen">
        <main className="max-w-[1200px] mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
