"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useSyncExternalStore } from "react";
import { useT } from "@/lib/i18n/client";

const subscribe = () => () => {};

export function ThemeToggle() {
  const tr = useT();
  const { resolvedTheme, setTheme } = useTheme();
  // Avoid a hydration mismatch: the real theme is only known on the client.
  const mounted = useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
  const isDark = mounted && resolvedTheme === "dark";

  return (
    <button
      type="button"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      aria-label={tr.nav.toggleTheme}
      title={isDark ? tr.nav.themeLight : tr.nav.themeDark}
      className="hover:bg-muted inline-flex size-10 items-center justify-center rounded-md"
    >
      {isDark ? (
        <Sun className="size-5" aria-hidden />
      ) : (
        <Moon className="size-5" aria-hidden />
      )}
    </button>
  );
}
