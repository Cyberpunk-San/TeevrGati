import { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
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
  title: "TeevrGati · BPCL Mathura Refinery",
  description:
    "AI diagnostics platform for BPCL Mathura Refinery — closed-loop decision support connecting manuals, sensor telemetry, and operator tacit knowledge.",
  themeColor: "#09090b",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <meta name="color-scheme" content="dark" />
      </head>
      <body className="min-h-full flex flex-col bg-[#09090b] text-[#fafafa]">
        <NavigationWrapper>{children}</NavigationWrapper>
      </body>
    </html>
  );
}
