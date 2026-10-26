import { ErrorState } from "@/components/ui/states";
import { tr } from "@/lib/i18n/tr";

export default function NotFound() {
  return <ErrorState title={tr.states.notFoundTitle} body={tr.states.notFoundBody} />;
}
