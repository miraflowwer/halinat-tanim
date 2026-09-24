import type { Language } from "@tanim/types";
import { CropDetailPage } from "../crops/CropDetailPage";
import { CropLibraryPage } from "../crops/CropLibraryPage";
import { PriceHistoryPage } from "../prices/PriceHistoryPage";
import { SuitabilityPage } from "../suitability/SuitabilityPage";
import { SupplyMapPage } from "../supply-map/SupplyMapPage";
import { WeatherPage } from "../weather/WeatherPage";

/** Routes owned by Phase 6. The Phase 5 authenticated shell can render this component. */
export function Phase6UtilityRoutes({
  path,
  language,
}: {
  path: string;
  language: Language;
}) {
  const pathname = path.split("?", 1)[0].replace(/\/$/, "") || "/";
  if (pathname === "/crops") return <CropLibraryPage language={language} />;
  if (pathname.startsWith("/crops/")) {
    return <CropDetailPage cropId={decodeURIComponent(pathname.slice("/crops/".length))} language={language} />;
  }
  if (pathname === "/prices") return <PriceHistoryPage language={language} />;
  if (pathname === "/suitability") return <SuitabilityPage language={language} />;
  if (pathname === "/map" || pathname === "/supply-map") return <SupplyMapPage language={language} />;
  if (pathname === "/weather") return <WeatherPage language={language} />;
  return null;
}
