import { AlertTriangle, Inbox } from "lucide-react";
import Link from "next/link";
import { tr } from "@/lib/i18n/tr";
import { cn } from "@/lib/utils";

interface StateProps {
  title: string;
  body?: string;
  className?: string;
  children?: React.ReactNode;
}

function StateShell({
  icon,
  title,
  body,
  className,
  children,
}: StateProps & { icon: React.ReactNode }) {
  return (
    <div
      className={cn(
        "bg-card flex flex-col items-center gap-2 rounded-lg border border-dashed px-6 py-10 text-center",
        className,
      )}
    >
      <div className="text-muted-foreground">{icon}</div>
      <h2 className="font-display text-xl font-semibold">{title}</h2>
      {body ? <p className="text-muted-foreground max-w-md text-sm">{body}</p> : null}
      {children}
    </div>
  );
}

export function EmptyState(props: StateProps) {
  return <StateShell {...props} icon={<Inbox className="size-8" aria-hidden />} />;
}

export function ErrorState({
  title = tr.states.errorTitle,
  body = tr.states.errorBody,
  onRetry,
  className,
}: {
  title?: string;
  body?: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div role="alert">
      <StateShell
        title={title}
        body={body}
        className={className}
        icon={<AlertTriangle className="text-accent size-8" aria-hidden />}
      >
        {onRetry ? (
          <button
            type="button"
            onClick={onRetry}
            className="bg-primary text-primary-foreground mt-2 h-10 rounded-md px-4 text-sm font-medium"
          >
            {tr.states.retry}
          </button>
        ) : (
          <Link href="/" className="text-primary mt-2 text-sm font-medium underline">
            {tr.states.backHome}
          </Link>
        )}
      </StateShell>
    </div>
  );
}
