"use client"
import * as React from 'react';
import { cn } from '@/lib/utils';
import { Button, type ButtonProps } from '@/components/ui/button';
import { useRouter } from 'next/navigation';
import { ChevronLeft } from 'lucide-react';
import { useTranslations } from 'next-intl';
export const BackButton = React.forwardRef<
  HTMLButtonElement,
  ButtonProps & { backLink?: string }
>(({ className, onClick, children, backLink = '/', ...props }, ref) => {
  const router = useRouter();
  const t  = useTranslations("NavMenu"); 
  return (
    <Button
      className={cn('', className)}
      variant="outline"
      size="sm"
      ref={ref}
      onClick={(e) => {
        if (window.history.length <= 1) {
          router.push(backLink);
        } else {
          router.back();
        }
        onClick?.(e);
      }}
      {...props}
    >
      {children ?? <ChevronLeft />}
      {t("back")}
    </Button>
  );
});
BackButton.displayName = 'BackButton';
