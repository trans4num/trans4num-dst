"use client"

import { LogOut } from "lucide-react"
import { useTranslations } from "next-intl"
import { useRouter } from "next/navigation"

import { useAuth } from "@/components/auth-provider"
import { Button } from "@/components/ui/button"

export const LogoutButton = ({ showLabel }: { showLabel: boolean }) => {
  const router = useRouter()
  const t = useTranslations("LoginForm")
  const { logout } = useAuth()

  const handleLogout = async () => {
    logout()
    router.replace("/login")
    router.refresh()
  }

  return (
    <Button
      type="button"
      variant="ghost"
      className="w-full justify-start gap-2"
      onClick={handleLogout}
    >
      <LogOut className="h-4 w-4" />
      {showLabel ? <span>{t("signOut")}</span> : null}
    </Button>
  )
}
