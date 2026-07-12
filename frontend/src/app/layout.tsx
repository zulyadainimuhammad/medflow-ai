import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MedFlow AI",
  description: "Engineering foundation for MedFlow AI frontend",
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
