import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { type AlternativeModel } from "@/models/alternative";
import { Box, TrendingUp } from "lucide-react";
import { useTranslations } from "next-intl";
import { GoalTypeBadge } from "@/components/goal-type-badge";
import { motion } from "framer-motion";

export function AlternativeResultCard({
  name,
  alternativeModel,
}: {
  name: string;
  alternativeModel: AlternativeModel;
}) {
  const t = useTranslations("Alternative");
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card className="w-full">
        <CardHeader>
          <div className="flex items-center  justify-between">
            <div className="flex items-center space-x-2">
              <Box className="h-6 w-6" />
              <CardTitle className="pr-2">
                <p>{name}</p>
              </CardTitle>
            </div>
            <GoalTypeBadge goal={alternativeModel?.goal} />
          </div>
        </CardHeader>
        <CardContent>
          {alternativeModel?.goal?.configuration?.length > 0 ? (
            <>
              {alternativeModel.goal.configuration.map((configuration) => (
                <div key={configuration.name} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <TrendingUp className="h-5 w-5 text-green-600" />
                    <span className="font-semibold">
                      {t("value_range_names." + alternativeModel.goal.type)}
                    </span>
                  </div>
                  <div className="flex items-center justify-center">
                    <Badge variant="outline" className={configuration.value > 0 ? "text-green-600" : "text-red-600"}>
                      {configuration.value > 0 ? "+" : null}
                      {configuration.value}%
                    </Badge>
                  </div>
                </div>
              ))}
            </>
          ) : (
            <div className="flex items-center justify-center">
              <p className="text-sm text-gray-500">{t("noConfiguration")}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
