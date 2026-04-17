import { Route, Routes } from "react-router-dom";

import HomePage from "@/app/page";
import LoginPage from "@/app/login/page";
import AlternativesPage from "@/app/region/alternatives/page";
import AlternativePage from "@/app/region/alternative/page";
import CreateAlternativePage from "@/app/region/create-alternative/page";
import ChooseRegionPage from "@/app/region/page";
import { Providers } from "@/app/providers";
import { TanstackQueryProviders } from "@/app/tanstack-query-providers";
import RegionLayout from "@/app/region/layout";

function RegionShell({ children }: { children: React.ReactNode }) {
  return <RegionLayout>{children}</RegionLayout>;
}

export default function App() {
  return (
    <Providers>
      <TanstackQueryProviders>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/region"
            element={
              <RegionShell>
                <ChooseRegionPage />
              </RegionShell>
            }
          />
          <Route
            path="/region/"
            element={
              <RegionShell>
                <ChooseRegionPage />
              </RegionShell>
            }
          />
          <Route
            path="/region/alternatives/"
            element={
              <RegionShell>
                <AlternativesPage />
              </RegionShell>
            }
          />
          <Route
            path="/region/alternative/"
            element={
              <RegionShell>
                <AlternativePage />
              </RegionShell>
            }
          />
          <Route
            path="/region/create-alternative/"
            element={
              <RegionShell>
                <CreateAlternativePage />
              </RegionShell>
            }
          />
        </Routes>
      </TanstackQueryProviders>
    </Providers>
  );
}
