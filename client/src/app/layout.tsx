import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "System Design Lab",
  description: "Demo client for the design running in the local cluster",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header>
          <strong>System Design Lab</strong>
          <nav>
            <a href="http://grafana.localhost:8080" target="_blank" rel="noreferrer">
              Grafana
            </a>
            <a href="http://chaos.localhost:8080" target="_blank" rel="noreferrer">
              Chaos Mesh
            </a>
          </nav>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
