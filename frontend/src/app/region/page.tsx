"use client";

import { Loader2 } from "lucide-react";
import { useTranslations } from "next-intl";

import DisclaimerDialog from "@/components/disclaimer-dialog";
import RegionCard from "@/components/region-card";
import { useRegions } from "@/hooks/use-region";

const ChooseRegionPage = () => {
  const t = useTranslations("RegionPage");
  const { regions, isLoading } = useRegions();

  return (
    <div className="container mx-auto px-4 py-8">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold">{t("chooseRegion")}</h1>
        <p className="mt-2 text-muted-foreground">{t("chooseRegionDescription")}</p>
      </header>
      <div className="flex gap-4 items-center justify-center flex-wrap">
        {isLoading ? (
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        ) : (
          regions?.map((region) => <RegionCard region={region} key={region.id} />)
        )}
      </div>
      <DisclaimerDialog />
    </div>
  );
};

export default ChooseRegionPage;
