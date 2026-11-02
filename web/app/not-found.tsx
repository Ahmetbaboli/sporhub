import { ErrorState } from "@/components/ui/states";
import { initLocale, t } from "@/lib/i18n";

export default async function NotFound() {
  await initLocale();
  const { states } = t();
  return (
    <ErrorState labels={states} title={states.notFoundTitle} body={states.notFoundBody} />
  );
}
