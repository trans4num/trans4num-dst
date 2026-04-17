"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

export function useStableQueryParam(name: string) {
  const searchParams = useSearchParams();
  const [value, setValue] = useState<string | null | undefined>(undefined);

  useEffect(() => {
    const fromWindow = new URLSearchParams(window.location.search).get(name);
    const fromRouter = searchParams.get(name);

    setValue(fromWindow ?? fromRouter);
  }, [name, searchParams]);

  return value;
}
