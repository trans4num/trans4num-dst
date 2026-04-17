"use client";

import { motion } from "framer-motion";
import { Loader } from "lucide-react";
import { Layer, Map, type MapMouseEvent, Source } from "@vis.gl/react-maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import AlternativeDetailsCollapsible from "@/components/alternative-details-collapsible";
import DataTypeSelect from "@/components/data-type-select";
import FieldMetadataLegend from "@/components/field-metadata-legend";
import HoverInfoCard from "@/components/field-hover-card";
import ToggleMapColorButton from "@/components/toggle-map-color-button";
import { Card } from "@/components/ui/card";
import { useAlternatives } from "@/hooks/use-alternative";
import { useFieldMetadata } from "@/hooks/use-field-metadata";
import { useRegion } from "@/hooks/use-region";
import { useSingleAlternative } from "@/hooks/use-single-alternative";
import { useStableQueryParam } from "@/hooks/use-stable-query-param";
import { generateNumericColor } from "@/lib/colors";
import { PUBLIC_CONFIG } from "@/lib/public-config";
import { buildAlternativesRoute } from "@/lib/routes";
import { cn } from "@/lib/utils";

type HoverInfo = {
  feature: GeoJSON.Feature<GeoJSON.Geometry>;
  x: number;
  y: number;
  color: string;
  id: string;
  value: string;
  statusQuoValue: string;
} | null;

export default function AlternativePage() {
  const router = useRouter();
  const regionId = useStableQueryParam("regionId");
  const alternativeId = useStableQueryParam("id");
  const [selectedType, setSelectedType] = useState("crop");
  const [colorMode, setColorMode] = useState("alternative");
  const [hoverInfo, setHoverInfo] = useState<HoverInfo>(null);

  useEffect(() => {
    if (regionId === undefined || alternativeId === undefined) {
      return;
    }

    if (regionId === null) {
      router.replace("/region");
      return;
    }

    if (alternativeId === null) {
      router.replace(buildAlternativesRoute(regionId));
    }
  }, [alternativeId, regionId, router]);

  const { statusQuo, isLoading: isStatusQuoLoading } = useAlternatives(regionId ?? undefined);
  const statusQuoId = statusQuo?.id ?? null;
  const {
    alternative,
    isLoading: isAlternativeLoading,
    error: alternativeError,
  } = useSingleAlternative(regionId ?? "", alternativeId ?? "");
  const {
    region,
    isLoading: isRegionLoading,
    error: regionError,
  } = useRegion(regionId ?? "");
  const {
    metadata,
    isLoading: isMetadataLoading,
    error: metadataError,
  } = useFieldMetadata(selectedType, alternativeId ?? "");
  const { metadata: statusQuoMetadata, isLoading: isStatusQuoMetadataLoading } =
    useFieldMetadata(selectedType, statusQuoId || "");

  const isDataLoading =
    isMetadataLoading ||
    isRegionLoading ||
    isAlternativeLoading ||
    isStatusQuoLoading ||
    ((colorMode === "statusQuo" || colorMode === "comparison") &&
      !!statusQuoId &&
      isStatusQuoMetadataLoading);

  const fieldColors = useMemo(() => {
    if (isMetadataLoading || !metadata) {
      return {};
    }

    return metadata.reduce((acc, field) => {
      acc[field.fieldId] = field.color;
      return acc;
    }, {} as Record<string, string>);
  }, [metadata, isMetadataLoading]);

  const statusQuoColors = useMemo(() => {
    if (!statusQuoMetadata) {
      return {};
    }

    return statusQuoMetadata.reduce((acc, field) => {
      acc[field.fieldId] = field.color;
      return acc;
    }, {} as Record<string, string>);
  }, [statusQuoMetadata]);

  const legendMap = useMemo(() => {
    if (isMetadataLoading || !metadata) {
      return {};
    }

    return metadata.reduce((acc, field) => {
      acc[field.value] = field.color;
      return acc;
    }, {} as Record<string, string>);
  }, [metadata, isMetadataLoading]);

  const minMaxValue = useMemo(() => {
    if (isMetadataLoading || !metadata || selectedType === "crop") {
      return { min: 0, max: 0 };
    }

    return {
      min: Math.min(...metadata.map((field) => Number(field.value))),
      max: Math.max(...metadata.map((field) => Number(field.value))),
    };
  }, [isMetadataLoading, metadata, selectedType]);

  const metadataMap = useMemo(() => {
    if (!metadata) return {};

    return metadata.reduce((acc, field) => {
      acc[field.fieldId] = field.value;
      return acc;
    }, {} as Record<string, string | number>);
  }, [metadata]);

  const statusQuoMap = useMemo(() => {
    if (!statusQuoMetadata) return {};

    return statusQuoMetadata.reduce((acc, field) => {
      acc[field.fieldId] = field.value;
      return acc;
    }, {} as Record<string, string | number>);
  }, [statusQuoMetadata]);

  const onHover = useCallback((event: MapMouseEvent) => {
    const {
      features,
      point: { x, y },
    } = event;
    const hoveredFeature = features && features[0];

    if (hoveredFeature) {
      const { id, color, value, statusQuoValue } = hoveredFeature.properties;
      setHoverInfo({
        feature: hoveredFeature,
        x,
        y,
        id,
        color,
        value,
        statusQuoValue,
      });
    } else {
      setHoverInfo(null);
    }
  }, []);

  const processedData = useMemo(() => {
    if (!region?.fields) return null;

    return {
      ...region.fields,
      features: region.fields.features.map((feature) => {
        if (feature.id === undefined) return feature;
        const id = feature.id.toString();
        let color = "#cccccc";

        if (colorMode === "alternative") {
          color = fieldColors[id] || "#cccccc";
        } else if (colorMode === "statusQuo") {
          color = statusQuoColors[id] || "#cccccc";
        } else if (colorMode === "comparison") {
          const altVal = metadataMap[id];
          const statusVal = statusQuoMap[id];

          if (typeof altVal === "number" && typeof statusVal === "number") {
            const diff = statusVal === 0 ? 1 : altVal / statusVal;
            const colorScheme = selectedType === "nLoad" ? "greenToRed" : "redToGreen";
            color = generateNumericColor(diff, 0, 2, colorScheme);
          } else {
            color = altVal === statusVal ? "grey" : "green";
          }
        }

        return {
          ...feature,
          properties: {
            id,
            color,
            value: metadataMap[id],
            statusQuoValue: statusQuoMap[id],
          },
        };
      }),
    };
  }, [
    region?.fields,
    fieldColors,
    statusQuoColors,
    metadataMap,
    statusQuoMap,
    colorMode,
    selectedType,
  ]);

  if (
    regionId === undefined ||
    alternativeId === undefined ||
    regionId === null ||
    alternativeId === null
  ) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader className="animate-spin text-gray-700" />
      </div>
    );
  }

  if (metadataError) {
    console.error(metadataError);
  }
  if (alternativeError || regionError) {
    console.error("Loading errors", alternativeError, regionError);
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-red-500 p-4 border border-red-200 rounded bg-red-50">Fejl</div>
      </div>
    );
  }

  return (
    <div className="relative flex-1 h-full">
      <AlternativeDetailsCollapsible alternative={alternative} statusQuo={statusQuo} />
      <div className="h-full pb-4">
        <Card className="h-full overflow-hidden">
          {region ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="h-full"
            >
              <div className="grid grid-cols-1 grid-rows-1 items-center justify-center relative h-full">
                {isDataLoading ? (
                  <div className="absolute inset-0 bg-white bg-opacity-60 flex items-center justify-center z-20">
                    <Loader className="animate-spin text-gray-700" />
                  </div>
                ) : null}
                {metadataError ? (
                  <div className="absolute inset-0 bg-white bg-opacity-60 flex items-center justify-center z-20">
                    <div className="flex items-center justify-center h-full">
                      <div className="text-red-500 p-4 border border-red-200 rounded bg-red-50">Fejl</div>
                    </div>
                  </div>
                ) : null}
                <div className="col-start-1 col-end-2 row-start-1 row-end-2 justify-self-end self-start p-4 z-10 flex flex-col gap-2 h-full">
                  <DataTypeSelect onValueChange={setSelectedType} value={selectedType} />
                  <div className="min-h-0">
                    {colorMode !== "comparison" ? (
                      <FieldMetadataLegend
                        values={legendMap}
                        type={selectedType === "crop" ? "categorical" : "numeric"}
                        minValue={minMaxValue.min}
                        maxValue={minMaxValue.max}
                        colorScheme={selectedType === "nLoad" ? "blueToRed" : "redToGreen"}
                        getColor={generateNumericColor}
                      />
                    ) : (
                      <FieldMetadataLegend
                        values={{
                          "No change": "grey",
                          Changed: "green",
                        }}
                        type={selectedType === "crop" ? "categorical" : "numeric"}
                        minValue={0}
                        maxValue={2}
                        colorScheme={selectedType === "nLoad" ? "greenToRed" : "redToGreen"}
                        getColor={generateNumericColor}
                      />
                    )}
                  </div>
                  <ToggleMapColorButton colorMode={colorMode} onChange={setColorMode} />
                </div>

                <div
                  className={cn(
                    "col-start-1 col-end-2 row-start-1 row-end-2 h-full transition-all transition-duration-1000",
                    isDataLoading ? "blur-sm" : "",
                  )}
                >
                  <Map
                    initialViewState={region.initialViewState}
                    style={{ width: "100%", height: "100%" }}
                    interactiveLayerIds={["field-data"]}
                    onMouseMove={onHover}
                    mapStyle={PUBLIC_CONFIG.mapStyle}
                  >
                    {region.fields && processedData ? (
                      <Source type="geojson" data={processedData}>
                        <Layer
                          id="field-data"
                          type="fill"
                          paint={{
                            "fill-color": ["get", "color"],
                            "fill-opacity": 0.8,
                          }}
                        />
                      </Source>
                    ) : null}
                    {hoverInfo ? (
                      <HoverInfoCard
                        x={hoverInfo.x}
                        y={hoverInfo.y}
                        dataType={selectedType}
                        fieldId={hoverInfo.id}
                        alternativeValue={String(hoverInfo.value)}
                        statusQuoValue={String(hoverInfo.statusQuoValue)}
                      />
                    ) : null}
                  </Map>
                </div>
              </div>
            </motion.div>
          ) : null}
        </Card>
      </div>
    </div>
  );
}
