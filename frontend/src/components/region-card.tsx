
'use client';

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Globe } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import { type Region } from "@/models/region";
import { useTranslations } from "next-intl";
import { buildAlternativesRoute } from "@/lib/routes";

const RegionCard = ({ region }:{ region: Region}) => {
  const t = useTranslations("RegionPage")
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Link href={buildAlternativesRoute(region.id)} className="group">
        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader className="flex flex-row items-center space-x-4 p-4">
            <div className="rounded-full p-2">
              <Globe className="h-6 w-6 text-primary" />
            </div>
            <CardTitle className="text-lg">{region.name}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{t("alternativesFor")} {region.name}</p>
          </CardContent>
        </Card>
      </Link>
    </motion.div>
  );
};

export default RegionCard;
