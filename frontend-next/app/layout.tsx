import { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import NavigationWrapper from "./components/NavigationWrapper";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TeevrGati - Self-Healing Intelligence",
  description: "Closed-loop decision-support system connecting manuals, sensor telemetry, and operator tacit knowledge.",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-[#0b0f19] text-[#e2e8f0]">
        <NavigationWrapper>{children}</NavigationWrapper>
      </body>
    </html>
  );
}
