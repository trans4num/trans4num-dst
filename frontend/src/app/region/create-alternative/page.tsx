"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowUpRight, BarChart2, Droplets, Info, MapPinPlus, TrendingUp } from "lucide-react";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm, useWatch } from "react-hook-form";

import { GoalTypeCard } from "@/components/goal-type-card";
import SingleSlider from "@/components/single-slider";
import { SwitchGoalTypeDialog } from "@/components/switch-goal-type-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Form, FormField, FormItem, FormLabel } from "@/components/ui/form";
import { Switch } from "@/components/ui/switch";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useCreateAlternative } from "@/hooks/use-create-alternative";
import { useRegionModels } from "@/hooks/use-region-models";
import { useStableQueryParam } from "@/hooks/use-stable-query-param";
import { buildAlternativesRoute } from "@/lib/routes";
import { alternativeFormSchema, type AlternativeFormValues } from "@/models/alternative";

const goalTypeIcons = {
  maximizeEconomy: TrendingUp,
  minimizeNLoad: Droplets,
  maximizeEconomyNLoad: BarChart2,
} as const;

const getValueColor = (value: number) => {
  if (value === 0) return "text-gray-500";
  if (value > 0) return value > 50 ? "text-green-500" : "text-green-700";
  return value < -50 ? "text-red-500" : "text-red-600";
};

const fadeSlide = {
  initial: { opacity: 0, x: -20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 20 },
  transition: { duration: 0.3 },
} as const;

export default function CreateAlternativePage() {
  const t = useTranslations("Alternative");
  const tFields = useTranslations("AlternativeFields");
  const router = useRouter();
  const regionId = useStableQueryParam("regionId");
  const [newGoalType, setNewGoalType] = useState<string | null>(null);

  useEffect(() => {
    if (regionId === null) {
      router.replace("/region");
    }
  }, [regionId, router]);

  const { createAlternative, isPending } = useCreateAlternative(regionId ?? "");
  const { regionModels } = useRegionModels(regionId ?? "");

  const form = useForm<AlternativeFormValues>({
    resolver: zodResolver(alternativeFormSchema),
    defaultValues: {
      name: "",
      regionId: regionId ?? "",
      model: {
        goal: {
          name: "",
          description: "",
          type: "",
          configuration: [],
        },
        constraints: [],
      },
    },
  });

  useEffect(() => {
    if (regionId) {
      form.setValue("regionId", regionId);
    }
  }, [form, regionId]);

  const currentGoalType = useWatch({ control: form.control, name: "model.goal.type" });
  const selectedModel = regionModels?.models.find((model) => model.goal.type === currentGoalType);
  const currentConfiguration = selectedModel?.goal.configuration ?? [];
  const currentConstraints = selectedModel?.constraints ?? [];

  const handleGoalTypeChange = (type: string) => {
    const currentName = form.getValues("name");
    form.reset();
    form.setValue("regionId", regionId ?? "");
    form.setValue("model.goal.type", type);
    form.setValue("name", currentName);

    const newModel = regionModels?.models.find((model) => model.goal.type === type);
    if (newModel) {
      if (newModel.goal.configuration) {
        const configValues = newModel.goal.configuration.map((config) => ({
          name: config.name,
          enabled: true,
          value: config.value ?? 0,
          range: [config.range[0] ?? 0, config.range[1] ?? 100],
          unit: config.unit,
        }));
        form.setValue("model.goal.configuration", configValues);
      }
      if (newModel.constraints) {
        const constraintValues = newModel.constraints.map((constraint) => ({
          name: constraint.name,
          enabled: constraint.enabled,
          value: constraint.value ?? 0,
          range: [constraint.range[0] ?? 0, constraint.range[1] ?? 100],
          unit: constraint.unit,
        }));
        form.setValue("model.constraints", constraintValues);
      }
    }
  };

  const onGoalCardClick = (clickedType: string) => {
    if (!currentGoalType) {
      handleGoalTypeChange(clickedType);
    } else if (currentGoalType !== clickedType) {
      setNewGoalType(clickedType);
    }
  };

  async function onSubmit(data: AlternativeFormValues) {
    await createAlternative(data);
    if (regionId) {
      router.push(buildAlternativesRoute(regionId));
    }
  }

  if (regionId === undefined || regionId === null) {
    return null;
  }

  return (
    <div className="flex justify-center">
      <Card className="w-full">
        <CardHeader className="flex flex-row items-center justify-between">
          <div className="grid gap-2">
            <CardTitle className="flex items-center gap-2">
              <MapPinPlus className="size-4" /> {t("create_alternative")}
            </CardTitle>
            <CardDescription>{t("configure_model")}</CardDescription>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="w-full">
              <AnimatePresence mode="wait">
                <motion.div {...fadeSlide}>
                  <fieldset className="grid gap-6 rounded-lg border p-4 mb-4">
                    <legend className="-ml-1 px-1 text-sm font-medium">{t("goal_selection")}</legend>
                    <FormField
                      control={form.control}
                      name="model.goal.type"
                      render={({ field }) => (
                        <FormItem className="grid gap-4 space-y-0 md:grid-cols-3">
                          {regionModels?.models.map((model) => (
                            <GoalTypeCard
                              key={model.goal.type}
                              icon={goalTypeIcons[model.goal.type as keyof typeof goalTypeIcons]}
                              title={t(`goal_names.${model.goal.type}`)}
                              description={t(`goal_descriptions.${model.goal.type}`)}
                              selected={field.value === model.goal.type}
                              onClick={() => onGoalCardClick(model.goal.type)}
                            />
                          ))}
                        </FormItem>
                      )}
                    />
                  </fieldset>
                  <fieldset className="grid gap-6 rounded-lg border p-4">
                    <legend className="-ml-1 px-1 text-sm font-medium">{t("value_ranges")}</legend>
                    <AnimatePresence mode="wait">
                      {currentConfiguration.map((config, index) => (
                        <motion.div key={`${index}-${currentGoalType}`} {...fadeSlide}>
                          <FormField
                            control={form.control}
                            name={`model.goal.configuration.${index}`}
                            render={({ field }) => (
                              <FormItem className="flex gap-2 items-center">
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <FormLabel className="w-[10%] text-xs flex items-center gap-1">
                                      {t(`value_range_names.${currentGoalType}`)}
                                      <Info className="size-3 hover:text-gray-500" />
                                    </FormLabel>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    {t(`value_range_descriptions.${currentGoalType}`)}
                                  </TooltipContent>
                                </Tooltip>
                                <div className="w-[80%]">
                                  <SingleSlider
                                    value={field.value?.value ?? 0}
                                    onValueChange={(value) => field.onChange({ ...field.value, value })}
                                    min={config.range[0] ?? -100}
                                    max={config.range[1] ?? 100}
                                    step={1}
                                    showMiddleLine={true}
                                  />
                                </div>
                                <span
                                  className={`text-sm w-[10%] font-semibold ${getValueColor(
                                    field.value?.value ?? 0,
                                  )}`}
                                >
                                  {field.value?.value ?? 0}
                                  {config.unit}
                                </span>
                              </FormItem>
                            )}
                          />
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </fieldset>

                  <AnimatePresence mode="wait">
                    <motion.div key={currentGoalType} {...fadeSlide}>
                      <fieldset className="grid flex-1 gap-6 rounded-lg border p-4">
                        <legend className="-ml-1 px-1 text-sm font-medium">{t("constraints")}</legend>
                        {currentConstraints.map((constraint, index) => (
                          <FormField
                            key={`${constraint.name}-${currentGoalType}`}
                            control={form.control}
                            name={`model.constraints.${index}`}
                            render={({ field }) => (
                              <FormItem className="border rounded-lg">
                                <div className="flex items-center">
                                  <div className="flex items-center justify-between p-3 gap-2 flex-1">
                                    <FormLabel className="text-sm font-medium">
                                      {tFields(`fieldNames.${constraint.name}`)}
                                    </FormLabel>
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <Switch
                                          checked={field.value?.enabled ?? false}
                                          onCheckedChange={(checked: boolean) =>
                                            field.onChange({ ...field.value, enabled: checked })
                                          }
                                          className={
                                            field.value?.enabled
                                              ? "bg-green-500 data-[state=checked]:bg-green-500"
                                              : "bg-gray-300"
                                          }
                                        />
                                      </TooltipTrigger>
                                      <TooltipContent>
                                        {tFields(`fieldDescriptions.${constraint.name}`)}
                                      </TooltipContent>
                                    </Tooltip>
                                  </div>
                                  <div className="p-3 border-r border-l flex-[8.5]">
                                    <SingleSlider
                                      value={field.value?.value ?? 0}
                                      onValueChange={(value) => field.onChange({ ...field.value, value })}
                                      min={constraint.range[0] ?? 0}
                                      max={constraint.range[1] ?? 100}
                                      step={1}
                                      disabled={!field.value?.enabled}
                                    />
                                  </div>
                                  <div className="p-3 flex-[0.5] flex justify-end">
                                    <span
                                      className={`text-sm font-medium ${
                                        field.value?.enabled ? "text-gray-700" : "text-gray-300"
                                      }`}
                                    >
                                      {field.value?.value ?? 0}
                                      {constraint.unit}
                                    </span>
                                  </div>
                                </div>
                              </FormItem>
                            )}
                          />
                        ))}
                      </fieldset>
                    </motion.div>
                  </AnimatePresence>

                  <AnimatePresence mode="wait">
                    <motion.div {...fadeSlide}>
                      <fieldset className="grid gap-6 rounded-lg border p-4">
                        <legend className="-ml-1 px-1 text-sm font-medium">{t("name")}</legend>
                        <FormField
                          control={form.control}
                          name="name"
                          render={({ field }) => (
                            <FormItem>
                              <input
                                {...field}
                                className="w-full rounded-lg border p-2"
                                placeholder={t("alternative_name_placeholder")}
                              />
                            </FormItem>
                          )}
                        />
                      </fieldset>
                    </motion.div>
                  </AnimatePresence>
                </motion.div>
              </AnimatePresence>
              <div className="flex justify-end mt-4">
                <Button
                  type="submit"
                  disabled={isPending}
                  className="bg-green-400 hover:bg-green-500"
                >
                  {t("create_alternative")}
                  <ArrowUpRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
      <SwitchGoalTypeDialog
        handleGoalTypeChange={handleGoalTypeChange}
        newGoalType={newGoalType}
        setNewGoalType={setNewGoalType}
      />
    </div>
  );
}
