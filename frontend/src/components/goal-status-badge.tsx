import { Badge } from "@/components/ui/badge";
import { type Alternative } from "@/models/alternative";
import { useTranslations } from "next-intl";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

interface GoalStatusBadgeProps {
  status: Alternative["status"];
}

export function GoalStatusBadge({ status }: GoalStatusBadgeProps) {
    const t = useTranslations("HomePage.columns")

    if (status === "processing") status = "pending";

    return (

    <Tooltip>
      <TooltipTrigger>
        <Badge variant={status}>
          {t("statusValue." + status)}
        </Badge>
      </TooltipTrigger>
      <TooltipContent>
        {t("statusDescription." + status)}
      </TooltipContent>
    </Tooltip>
  )
}
