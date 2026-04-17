import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { DialogHeader } from "@/components/ui/dialog";
import { useTranslations } from "next-intl";
import { type Alternative } from "@/models/alternative";
import ConstraintsDisplayCard from "@/components/constraints-display-card";

interface AlternativeConfigurationDialogProps {
  alternative: Alternative;
  setAlternative: (alternative: Alternative | null) => void;
}

export function AlternativeConfigurationDialog({ alternative, setAlternative }: AlternativeConfigurationDialogProps) {
    const t = useTranslations("HomePage");
  return (
    <Dialog open={!!alternative} onOpenChange={(open) => setAlternative(open ? alternative : null)}>
        <DialogContent>
            <DialogHeader>
                <DialogTitle>{t("AlternativeConfigurationDialog.title")}</DialogTitle>
            </DialogHeader>
            <DialogDescription asChild>
                <div className="text-sm text-muted-foreground flex flex-col gap-4">
                    {t("AlternativeConfigurationDialog.description", { name: alternative.name })}
                    {alternative.model && 
                    <ConstraintsDisplayCard 
                    alternativeModel={alternative.model} />}
                </div>
            </DialogDescription>
        </DialogContent>
    </Dialog>
  );
}