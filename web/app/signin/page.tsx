import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { signInWith } from "@/app/actions/account";
import { EmptyState } from "@/components/ui/states";
import { enabledProviders, type ProviderId } from "@/lib/auth-config";
import { tr } from "@/lib/i18n/tr";
import { authEnabled, getViewer } from "@/lib/session";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: tr.account.signIn };

const OAUTH_LABELS: Partial<Record<ProviderId, string>> = {
  github: "GitHub",
  google: "Google",
};

const BUTTON =
  "bg-card hover:bg-muted flex h-11 w-full items-center justify-center rounded-md border text-sm font-semibold";

type Props = { searchParams: Promise<{ callbackUrl?: string }> };

export default async function SignInPage({ searchParams }: Props) {
  const { callbackUrl = "/me" } = await searchParams;
  if (!authEnabled()) return <EmptyState title={tr.account.unavailable} />;
  if (await getViewer()) redirect("/me");

  const providers = enabledProviders(process.env);
  return (
    <div className="mx-auto max-w-sm py-8">
      <h1 className="font-display text-4xl font-bold tracking-tight uppercase">
        {tr.account.signInTitle}
      </h1>
      <p className="text-muted-foreground mt-2 mb-6 text-sm">{tr.account.signInBody}</p>
      <div className="space-y-3">
        {providers.map((provider) => {
          const label = OAUTH_LABELS[provider];
          return (
            <form
              key={provider}
              action={signInWith.bind(null, provider)}
              className="space-y-2"
            >
              <input type="hidden" name="callbackUrl" value={callbackUrl} />
              {label ? (
                <button type="submit" className={BUTTON}>
                  {tr.account.continueWith(label)}
                </button>
              ) : (
                <fieldset className="space-y-2 rounded-md border border-dashed p-3">
                  <label htmlFor="dev-name" className="block text-xs font-medium">
                    {tr.account.devName}
                  </label>
                  <input
                    id="dev-name"
                    name="name"
                    required
                    maxLength={40}
                    className="bg-background h-10 w-full rounded-md border px-3 text-sm"
                  />
                  <button type="submit" className={BUTTON}>
                    {tr.account.devSubmit}
                  </button>
                </fieldset>
              )}
            </form>
          );
        })}
      </div>
    </div>
  );
}
