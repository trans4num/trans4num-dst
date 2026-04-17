"use client";

import logoPicture from "@/assets/images/trans4num-logo-RBG.png";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenuButton,
  SidebarRail,
  useSidebar,
} from "@/components/ui/sidebar";
import { MapIcon, MapPinPlus, Package } from "lucide-react";
import { useTranslations } from "next-intl";
import Image from "next/image";
import { useSearchParams } from "next/navigation";
import * as React from "react";
import { NavMain } from "@/components/nav-main";
import LocaleSwitcher from "@/components/locale-switcher";
import { LogoutButton } from "@/components/logout-button";
import { buildAlternativesRoute, buildCreateAlternativeRoute } from "@/lib/routes";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const t = useTranslations("NavMenu");
  const searchParams = useSearchParams();
  const { open } = useSidebar();
  const regionId = searchParams.get("regionId");

  const data = {
    navMain: [
      {
        groupings: [
          {
            groupingid: "regions",
            title: t("regions"),
            items: [
              {
                title: t("chooseRegion"),
                url: "/region",
                icon: MapIcon,
                isActive: true,
              },
            ],
          },
          ...(regionId ? [
            {
            groupingid: "alternatives",
            title: t("my_alternatives"),
            items: [
              {
                title: t("my_models"),
                  url: buildAlternativesRoute(regionId),
                icon: Package,
                  isActive: regionId ?? false,
              },
              {
                title: t("create_new_alternative"),
                  url: buildCreateAlternativeRoute(regionId),
                icon: MapPinPlus,
                  isActive: regionId ?? false,
              },
            ],
          },
          ] : []),
        ],
      },
    ],
  };

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenuButton
          size="lg"
          className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
        >
          <Image src={logoPicture} alt="Trans4num DST" width={50} height={50} />
          <div className="grid flex-1 text-left text-sm leading-tight">
            <span className="truncate font-semibold">DST</span>
            <span className="truncate text-xs">v1.0.0</span>
          </div>
        </SidebarMenuButton>
      </SidebarHeader>
      <SidebarContent>
        <NavMain data={data.navMain[0]} />
      </SidebarContent>
      <SidebarFooter>
        <LocaleSwitcher />
        <LogoutButton showLabel={open} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
