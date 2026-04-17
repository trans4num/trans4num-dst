"use client";

import {
    AlertDialog,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { Field, FieldContent, FieldError, FieldLabel } from "@/components/ui/field";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/auth-provider";

const DISCLAIMER_ACCEPTED_KEY = "disclaimer-accepted";

export default function DisclaimerDialog() {
    const t = useTranslations("DisclaimerDialog");
    const router = useRouter();
    const { logout } = useAuth();
    const [acceptedTerms, setAcceptedTerms] = useState(false);
    const [error, setError] = useState(false);
    const [open, setOpen] = useState(false);

    useEffect(() => {
        if (sessionStorage.getItem(DISCLAIMER_ACCEPTED_KEY) !== "true") {
            setOpen(true);
        }
    }, []);

    const onConfirm = () => {
        if (acceptedTerms) {
            sessionStorage.setItem(DISCLAIMER_ACCEPTED_KEY, "true");
            setOpen(false);
        } else setError(true);
    };

    const onCancel = () => {
        logout();
        router.replace("/login");
        router.refresh();
    };
    return (
        <AlertDialog open={open} onOpenChange={setOpen}>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>{t("title")}</AlertDialogTitle>
                    <AlertDialogDescription>{t("description")}</AlertDialogDescription>
                    <Field orientation="horizontal" data-invalid={error} className="pt-2">
                        <Checkbox
                            id="disclaimer-checkbox"
                            name="disclaimer-checkbox"
                            checked={acceptedTerms}
                            onCheckedChange={(checked: boolean) => {
                                setAcceptedTerms(checked);
                                if (checked) setError(false);
                            }}
                        />
                        <FieldContent>
                            <FieldLabel className={`text-sm ${error ? "font-bold" : ""}`}>
                                {t("acceptTerms")}
                            </FieldLabel>
                            {error && <FieldError>{t("acceptTermsError")}</FieldError>}
                        </FieldContent>
                    </Field>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <Button variant="outline" onClick={onCancel}>
                        {t("cancel")}
                    </Button>
                    <Button variant="default" 
                    className="bg-gradient-to-br from-[#3d66a7] via-[#3d66a7] to-[#2fb393]" 
                    onClick={onConfirm}>
                        {t("confirm")}
                    </Button>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    );
}
