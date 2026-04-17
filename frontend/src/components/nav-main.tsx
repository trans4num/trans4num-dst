"use client"

import { type LucideIcon } from "lucide-react"
import { SidebarGroup, SidebarGroupLabel, SidebarMenu, SidebarMenuButton } from "@/components/ui/sidebar"
import Link from "next/link"
import { usePathname } from "next/navigation"

export function NavMain({ data }: { data: { groupings: { groupingid: string, title: string, items: { title: string, url: string, icon: LucideIcon }[] }[] } }) {
  const pathname = usePathname()

  return (
    <>
      {data.groupings.map((grouping) => (
        <SidebarGroup key={grouping.groupingid}>
          <SidebarGroupLabel>{grouping.title}</SidebarGroupLabel>
          <SidebarMenu>
            {grouping.items.map((item) => (
              <Link href={item.url} key={item.title}>
                <SidebarMenuButton
                  isActive={pathname === item.url.split("?")[0]}
                  key={item.title}
                  tooltip={item.title}
                >
                {item.icon && <item.icon />}
                  <span>{item.title}</span>
                </SidebarMenuButton>
              </Link>
            ))}
          </SidebarMenu>
        </SidebarGroup>
      ))}
    </>
  )
}
