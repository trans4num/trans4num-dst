import { type Alternative } from "@/models/alternative";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { ChevronDown, Loader, ChartPie} from "lucide-react";
import { AlternativeResultCard } from "@/components/alternative-result-card";
import ConstraintsDisplayCard from "@/components/constraints-display-card";
import PieChartCard from "@/components/crop-pie-chart-card";
import { useTranslations } from "next-intl";

interface AlternativeDetailsCollapsibleProps {
    alternative?: Alternative;
    statusQuo?: Alternative;
}

export default function AlternativeDetailsCollapsible({alternative, statusQuo}: AlternativeDetailsCollapsibleProps) {
    const t = useTranslations("Alternative");
    if (!alternative || !statusQuo || !alternative.model) {
        return (
          <div className="flex items-center justify-center h-full w-full">
            <Loader className="animate-spin text-gray-700" />
          </div>
        );
      }
    return (
        <Collapsible defaultOpen={true} className="absolute top-2 left-2 z-20 rounded-lg flex flex-col max-h-[calc(100vh-6rem)]">
              <CollapsibleTrigger asChild>
                <Button variant="outline" className="group min-w-[600px] w-[33vw] h-16 rounded-xl">
                    <span className="flex items-center justify-between w-full text-lg">
                    <ChartPie className="mr-2 size-6 " /> {t("alternativeOverview")}
                    <ChevronDown className="ml-auto group-data-[state=open]:rotate-180 size-6" />
                    </span>
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="overflow-hidden origin-top will-change-transform data-[state=open]:animate-collapsible-down data-[state=closed]:animate-collapsible-up">
                <div className="flex flex-col min-w-[600px] w-[33vw] gap-y-2 overflow-y-auto scrollbar-hidden max-h-[calc(100vh-8rem)] pb-4">
                  <AlternativeResultCard
                    name={alternative.name}
                    alternativeModel={alternative.model}
                  />
                  <ConstraintsDisplayCard alternativeModel={alternative.model} />
                  <PieChartCard alternative={alternative} statusQuo={statusQuo} />
                </div>
              </CollapsibleContent>
            </Collapsible>
    );
}