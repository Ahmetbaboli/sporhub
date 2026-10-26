import type { Metadata, Viewport } from "next";
import { Barlow_Condensed, Geist } from "next/font/google";
import { Footer } from "@/components/layout/footer";
import { Header } from "@/components/layout/header";
import { ThemeProvider } from "@/components/layout/theme-provider";
import { tr } from "@/lib/i18n/tr";
import "./globals.css";

const sans = Geist({ variable: "--font-geist-sans", subsets: ["latin", "latin-ext"] });
const display = Barlow_Condensed({
  variable: "--font-display",
  subsets: ["latin", "latin-ext"],
  weight: ["500", "600", "700"],
});

export const metadata: Metadata = {
  title: {
    default: `${tr.app.name} — ${tr.app.tagline}`,
    template: `%s · ${tr.app.name}`,
  },
  description: tr.app.description,
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f5f2ea" },
    { media: "(prefers-color-scheme: dark)", color: "#0a100d" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="tr"
      suppressHydrationWarning
      className={`${sans.variable} ${display.variable}`}
    >
      <body className="flex min-h-dvh flex-col antialiased">
        <ThemeProvider>
          <a
            href="#main"
            className="bg-primary text-primary-foreground sr-only z-50 rounded px-3 py-2 focus:not-sr-only focus:absolute focus:top-2 focus:left-2"
          >
            {tr.app.skipToContent}
          </a>
          <Header />
          <main id="main" className="mx-auto w-full max-w-5xl flex-1 px-4 py-6 sm:py-8">
            {children}
          </main>
          <Footer />
        </ThemeProvider>
      </body>
    </html>
  );
}
