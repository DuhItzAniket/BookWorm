import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BookWorm",
  description: "Document question answering powered by retrieval and BERT.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
