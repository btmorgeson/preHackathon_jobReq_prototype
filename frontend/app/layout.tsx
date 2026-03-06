import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Job Req Candidate Ranker",
  description: "HR AI Hackathon Prototype",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
