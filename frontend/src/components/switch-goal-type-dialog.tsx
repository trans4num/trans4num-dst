import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { useTranslations } from "next-intl";


interface SwitchGoalTypeDialogProps {
  handleGoalTypeChange: (type: string) => void;
  newGoalType: string | null;
  setNewGoalType: (type: string | null) => void;
}

export function SwitchGoalTypeDialog({ handleGoalTypeChange, newGoalType, setNewGoalType }: SwitchGoalTypeDialogProps) {
  const t = useTranslations("Alternative");

  const onConfirmSwitch = () => {
    if (newGoalType){
      handleGoalTypeChange(newGoalType);
      setNewGoalType(null);
    }
  }

  const onCancelSwitch = () => {
    setNewGoalType(null);
  }
    return (
    <AlertDialog open={!!newGoalType} onOpenChange={(open: boolean) => !open && onCancelSwitch()}>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>{t("switch_goal_type_title")}</AlertDialogTitle>
      <AlertDialogDescription>
        {t("switch_goal_type_description")}
      </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
      <AlertDialogCancel onClick={onCancelSwitch} className="bg-secondary/10 hover:bg-secondary">
        {t("cancel")}
      </AlertDialogCancel>
      <AlertDialogAction onClick={onConfirmSwitch} className="bg-green-400 hover:bg-green-500">
        {t("confirm")}
      </AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
  )
}