import type { Metadata } from "next";
import "./globals.css";
import { PortalShell } from "@/components/PortalShell";

export const metadata: Metadata = {
  title: "Rook | Release reliability control plane",
  description: "Release safely. Detect failure. Recover with evidence.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><PortalShell>{children}</PortalShell></body></html>;
}
