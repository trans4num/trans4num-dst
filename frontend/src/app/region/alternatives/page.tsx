"use client";

import { DialogTitle } from "@radix-ui/react-dialog";
import { ArrowUpRight, Blend, Loader2, Map, Package } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslations } from "next-intl";

import AlternativeComparisonCard from "@/components/alternative-comparison-card";
import { AlternativesDataTable } from "@/components/alternatives-data-table";
import { AlernativeTableColumns } from "@/components/alternatives-data-table-columns";
import { TabNavigation } from "@/components/tabs";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { useAlternatives } from "@/hooks/use-alternative";
import { useStableQueryParam } from "@/hooks/use-stable-query-param";
import { buildAlternativeRoute, buildCreateAlternativeRoute } from "@/lib/routes";
import { type Alternative } from "@/models/alternative";

const TEN_SECONDS_IN_MILLISECONDS = 10000;
type TabKey = "completed" | "processing" | "all";

export default function AlternativesPage() {
  const t = useTranslations("HomePage");
  const router = useRouter();
  const regionId = useStableQueryParam("regionId");
  const [activeTab, setActiveTab] = useState<TabKey>("all");
  const [selectedAlternatives, setSelectedAlternatives] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (regionId === null) {
      router.replace("/region");
    }
  }, [regionId, router]);

  const tabs = [
    { key: "all" as TabKey, displayValue: t("tabs.all") },
    { key: "completed" as TabKey, displayValue: t("tabs.completed") },
    { key: "processing" as TabKey, displayValue: t("tabs.processing") },
  ];

  const { alternatives, statusQuo, isLoading } = useAlternatives(
    regionId ?? undefined,
    TEN_SECONDS_IN_MILLISECONDS,
  );

  const filteredAlternatives = useMemo(() => {
    if (!alternatives) return [];
    switch (activeTab) {
      case "completed":
        return alternatives.filter((alt) => alt.status === "success");
      case "processing":
        return alternatives.filter((alt) => alt.status === "processing");
      default:
        return alternatives;
    }
  }, [alternatives, activeTab]);

  const handleAlternativeToggle = useCallback((alternative: Alternative) => {
    setSelectedAlternatives((prev) => {
      const newSelected = new Set(prev);
      if (newSelected.has(alternative.id)) {
        newSelected.delete(alternative.id);
      } else {
        newSelected.add(alternative.id);
      }
      return newSelected;
    });
  }, []);

  const getRowLink = useCallback(
    (alternative: Alternative) => {
      if (!regionId) {
        return "/region";
      }
      return buildAlternativeRoute(regionId, alternative.id);
    },
    [regionId],
  );

  const columns = AlernativeTableColumns(handleAlternativeToggle, statusQuo, getRowLink);

  const selectedAlternativesArray = useMemo(
    () => filteredAlternatives.filter((alt) => selectedAlternatives.has(alt.id)),
    [filteredAlternatives, selectedAlternatives],
  );

  const handleTabChange = (index: number) => {
    setActiveTab(tabs[index].key);
    setSelectedAlternatives(new Set());
  };

  if (regionId === undefined || regionId === null) {
    return (
      <div className="flex h-[calc(100vh-8rem)] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-8rem)]">
      <div className="flex flex-col gap-4">
        <Card className="w-full flex flex-col">
          <CardHeader>
            <CardTitle className="flex flex-col gap-4">
              <h1 className="flex items-center gap-2">
                <Package /> {t("pageTitle")}
              </h1>
              <div className="flex items-center justify-between gap-2">
                <TabNavigation tabs={tabs} onTabChange={handleTabChange} />
                <div className="flex items-center gap-2">
                  <Link href={buildCreateAlternativeRoute(regionId)}>
                    <Button variant="outline" disabled={selectedAlternativesArray.length !== 1}>
                      {t("openAlternative")}
                      <Map className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button disabled={selectedAlternativesArray.length === 0} variant="outline">
                        {t("compareAlternatives")}
                        <Blend className="ml-2 h-4 w-4" />
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="w-full max-w-6xl mx-auto p-6 sm:p-8 md:p-10">
                      <DialogTitle className="hidden"></DialogTitle>
                      <AlternativeComparisonCard
                        statusQuo={statusQuo!}
                        selectedAlternatives={selectedAlternativesArray}
                      />
                    </DialogContent>
                  </Dialog>
                  <Link href={buildCreateAlternativeRoute(regionId)}>
                    <Button className="bg-green-400 hover:bg-green-500">
                      {t("addAlternative")}
                      <ArrowUpRight className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </div>
            </CardTitle>
          </CardHeader>
          <div className="flex-1 min-h-0">
            <CardContent className="flex">
              {isLoading ? (
                <div className="flex items-center justify-center w-full p-4">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                </div>
              ) : (
                <AlternativesDataTable
                  key={activeTab}
                  columns={columns}
                  getRowLink={getRowLink}
                  data={filteredAlternatives}
                  onRowSelect={handleAlternativeToggle}
                  selectedRow={null}
                />
              )}
            </CardContent>
          </div>
        </Card>
      </div>
    </div>
  );
}
