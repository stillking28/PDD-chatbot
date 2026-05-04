import type { ReactNode } from "react";
import "./globals.css";

export const metadata = {
  title: "PDD ChatBot",
  description: "Traffic rules cognitive offloader",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
