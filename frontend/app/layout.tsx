import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SentiNews",
  description: "Indian Stock Market Intelligence",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        suppressHydrationWarning
        className="min-h-screen bg-slate-950"
      >
        {children}
      </body>
    </html>
  );
}