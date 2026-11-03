import type { Metadata, Viewport } from "next";
import { Barlow_Condensed, Inter } from "next/font/google";
import { DemoBanner } from "@/components/layout/demo-banner";
import { Footer } from "@/components/layout/footer";
import { Header } from "@/components/layout/header";
import { ThemeProvider } from "@/components/layout/theme-provider";
import { TribuneProvider } from "@/components/tribune/tribune-provider";
import { initLocale, t } from "@/lib/i18n";
import { I18nProvider } from "@/lib/i18n/client";
import { PALETTE_BOOT_SCRIPT } from "@/lib/palettes";
import { getTribune } from "@/lib/tribune-server";
import "./globals.css";

// Inter for reading (full Turkish coverage via latin-ext); the condensed face only for big titles.
const sans = Inter({ variable: "--font-inter", subsets: ["latin", "latin-ext"] });
const display = Barlow_Condensed({
  variable: "--font-display",
  subsets: ["latin", "latin-ext"],
  weight: ["500", "600", "700"],
});

export async function generateMetadata(): Promise<Metadata> {
  await initLocale();
  const { app } = t();
  return {
    title: { default: `${app.name} — ${app.tagline}`, template: `%s · ${app.name}` },
    description: app.description,
  };
}

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f3f6fa" },
    { media: "(prefers-color-scheme: dark)", color: "#0b1018" },
  ],
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const locale = await initLocale();
  const tribune = await getTribune();
  return (
    <html
      lang={locale}
      suppressHydrationWarning
      className={`${sans.variable} ${display.variable}`}
    >
      <head>
        {/* Applies the saved colour palette before first paint. */}
        <script dangerouslySetInnerHTML={{ __html: PALETTE_BOOT_SCRIPT }} />
      </head>
      <body className="flex min-h-dvh flex-col antialiased">
        <I18nProvider locale={locale}>
          <ThemeProvider>
            <TribuneProvider initial={tribune}>
              <a
                href="#main"
                className="bg-primary text-primary-foreground sr-only z-50 rounded px-3 py-2 focus:not-sr-only focus:absolute focus:top-2 focus:left-2"
              >
                {t().app.skipToContent}
              </a>
              <DemoBanner />
              <Header />
              <main
                id="main"
                className="mx-auto w-full max-w-[80rem] flex-1 px-4 py-5 sm:px-6 sm:py-6"
              >
                {children}
              </main>
              <Footer />
            </TribuneProvider>
          </ThemeProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
