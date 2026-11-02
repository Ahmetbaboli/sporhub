"use client";

import { useActionState } from "react";
import { deleteAccountAction } from "@/app/actions/account";
import { useT } from "@/lib/i18n/client";

/** Irreversible: needs an explicit tick before the server action runs. */
export function DeleteAccountForm() {
  const tr = useT();
  const [state, action, pending] = useActionState(deleteAccountAction, null);
  return (
    <form action={action} className="space-y-3">
      <p className="text-sm">{tr.account.deleteBody}</p>
      <label className="flex items-start gap-2 text-sm">
        <input type="checkbox" name="confirm" value="yes" required className="mt-1" />
        {tr.account.deleteConfirm}
      </label>
      {state?.error ? (
        <p role="alert" className="text-accent text-sm">
          {state.error === "confirm"
            ? tr.account.deleteNeedsConfirm
            : tr.account.deleteFailed}
        </p>
      ) : null}
      <button
        type="submit"
        disabled={pending}
        className="border-accent text-accent hover:bg-accent hover:text-accent-foreground h-10 rounded-md border px-4 text-sm font-semibold disabled:opacity-60"
      >
        {tr.account.deleteButton}
      </button>
    </form>
  );
}
