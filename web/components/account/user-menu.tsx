import { LogIn, LogOut, UserRound } from "lucide-react";
import Link from "next/link";
import { signOutAction } from "@/app/actions/account";
import { tr } from "@/lib/i18n/tr";
import { authEnabled, getViewer } from "@/lib/session";

const ICON_BUTTON =
  "hover:bg-muted inline-flex size-10 items-center justify-center rounded-md";

export async function UserMenu() {
  if (!authEnabled()) return null;
  const viewer = await getViewer().catch(() => null);

  if (!viewer) {
    return (
      <Link
        href="/signin"
        className="hover:bg-muted inline-flex h-10 items-center gap-1.5 rounded-md px-3 text-sm font-medium"
      >
        <LogIn className="size-4" aria-hidden />
        {tr.account.signIn}
      </Link>
    );
  }
  return (
    <nav aria-label={tr.account.menu} className="flex items-center">
      <Link
        href="/me"
        className="hover:bg-muted inline-flex h-10 items-center gap-2 rounded-md px-2 text-sm font-medium"
      >
        {viewer.image ? (
          // eslint-disable-next-line @next/next/no-img-element -- avatars come from OAuth hosts
          <img src={viewer.image} alt="" className="size-7 rounded-full" />
        ) : (
          <UserRound className="size-5" aria-hidden />
        )}
        <span className="hidden sm:inline">{tr.account.myPage}</span>
      </Link>
      <form action={signOutAction}>
        <button
          type="submit"
          className={ICON_BUTTON}
          aria-label={tr.account.signOut}
          title={tr.account.signOut}
        >
          <LogOut className="size-5" aria-hidden />
        </button>
      </form>
    </nav>
  );
}
