import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "ClipForge",
  description: "Turn long videos into short, vertical, social-ready clips.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header style={{ padding: "16px 24px", borderBottom: "1px solid #eee" }}>
          <a href="/" style={{ fontWeight: 700, fontSize: 20, textDecoration: "none", color: "#111" }}>
            ClipForge
          </a>
        </header>
        <main style={{ maxWidth: 960, margin: "0 auto", padding: "24px" }}>{children}</main>
      </body>
    </html>
  );
}
