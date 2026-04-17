'use client';

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { useTranslations } from "next-intl";

import loginBackground from "@/assets/images/field-cow-forest.jpg";
import logoPicture from "@/assets/images/trans4num-logo-RBG.png";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth-provider";

export function LoginForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const router = useRouter();
  const t = useTranslations("LoginForm");
  const { login } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSignIn(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(username, password);
      router.push("/region");
      router.refresh();
    } catch (err) {
      console.error("Sign in error:", err);
      setError(err instanceof Error ? err.message : t("signinError"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card className="overflow-hidden">
        <CardContent className="grid p-0 md:grid-cols-2">
          <form className="p-6 md:p-8" onSubmit={handleSignIn}>
            <div className="flex flex-col gap-6">
              <div className="flex flex-col items-center text-center">
                <Image
                  src={logoPicture}
                  alt="Image"
                  className="w-1/4"
                />
                <p className="text-balance text-muted-foreground">
                  {t("appTitle")}
                </p>
                {error ? (
                  <p className="mt-2 text-sm text-red-600">{error}</p>
                ) : null}
              </div>
              <div className="grid gap-2">
                <Label htmlFor="username">{t("username")}</Label>
                <Input
                  id="username"
                  type="text"
                  placeholder={t("usernamePlaceholder")}
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <div className="flex items-center">
                  <Label htmlFor="password">{t("password")}</Label>
                </div>
                <Input
                  id="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-gradient-to-br from-[#3d66a7] via-[#3d66a7] to-[#2fb393]"
                disabled={loading}
              >
                {loading ? t("signingIn") : t("login")}
              </Button>
            </div>
          </form>
          <div className="relative hidden bg-muted md:block">
            <Image
              src={loginBackground}
              alt="Image"
              className="absolute inset-0 h-full w-full object-cover dark:brightness-[0.2] dark:grayscale"
            />
          </div>
        </CardContent>
      </Card>
      <div className="text-balance text-center text-xs text-muted-foreground [&_a]:underline [&_a]:underline-offset-4 hover:[&_a]:text-primary">
        {t("agreementText")} <a href="#">{t("termsOfService")}</a>{" "}
        {t("and")} <a href="#">{t("privacyPolicy")}</a>.
      </div>
    </div>
  );
}
