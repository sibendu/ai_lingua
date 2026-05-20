import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "AI Lingua",
  description: "French-first language practice for children.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
