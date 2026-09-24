import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { ApiClientError, apiRequest } from "@tanim/api-client";
import { frontendUrls } from "@tanim/config";
import { messages, phase5Messages } from "@tanim/i18n";
import type {
  AuthUser,
  AccountMembershipResponse,
  CooperativeAggregate,
  CooperativeOverview,
  CropLookup,
  GeographyLookup,
  Language,
  PlantingPlan,
  PlantingPlanInput,
  PlanningPeriod,
  RiskCheckResponse,
  RiskLevel,
} from "@tanim/types";
import type { CropListResponse } from "@tanim/types/phase6";
import { InternalLink, PlatformShell } from "./PlatformShell";
import { navigate } from "./navigation";
import { Phase6UtilityRoutes } from "./features/phase6/routes";

type PageProps = {
  language: Language;
  user: AuthUser;
  onLanguageChange: (value: Language) => void;
  onLogout: () => void;
};

type PageFrameProps = PageProps & { children: ReactNode };

type PlanFormValues = {
  crop_id: string;
  region_id: string;
  province_id: string;
  geography_id: string;
  area_ha: string;
  planting_date: string;
  period_key: string;
  comparison_crop_ids: string[];
};

const emptyPlanForm: PlanFormValues = {
  crop_id: "",
  region_id: "",
  province_id: "",
  geography_id: "",
  area_ha: "",
  planting_date: "",
  period_key: "",
  comparison_crop_ids: [],
};

function PageFrame({ language, user, onLanguageChange, onLogout, children }: PageFrameProps) {
  return (
    <PlatformShell
      language={language}
      user={user}
      onLanguageChange={onLanguageChange}
      onLogout={onLogout}
    >
      {children}
    </PlatformShell>
  );
}

function errorMessage(error: unknown, language: Language): string {
  const copy = phase5Messages[language];
  if (error instanceof ApiClientError) {
    const apiErrors = copy.errors as unknown as Record<string, string>;
    return apiErrors[error.code] ?? copy.genericError;
  }
  return copy.genericError;
}

function formatDate(value: string, language: Language): string {
  const locale = language === "tl" ? "tl-PH" : "en-PH";
  return new Intl.DateTimeFormat(locale, {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));
}

function formatPeriod(start: string, end: string, language: Language): string {
  const copy = phase5Messages[language];
  return `${formatDate(start, language)} ${copy.dateSeparator} ${formatDate(end, language)}`;
}

function formatArea(value: number, language: Language): string {
  return new Intl.NumberFormat(language === "tl" ? "tl-PH" : "en-PH", {
    maximumFractionDigits: 2,
  }).format(value);
}

function localizedCropName(language: Language, english: string, tagalog: string | null): string {
  return language === "tl" && tagalog ? tagalog : english;
}

function planStatusLabel(status: PlantingPlan["status"], language: Language): string {
  const copy = phase5Messages[language];
  if (status === "cancelled") return copy.statusCancelled;
  if (status === "completed") return copy.statusCompleted;
  return copy.statusActive;
}

function riskLabel(risk: RiskLevel, language: Language): string {
  return messages[language].riskLabels[risk];
}

function Metric({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="metric-card">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function PlanSummary({ plan, language }: { plan: PlantingPlan; language: Language }) {
  const copy = phase5Messages[language];
  return (
    <dl className="plan-summary">
      <Metric
        label={copy.crop}
        value={localizedCropName(language, plan.crop_name_en, plan.crop_name_tl)}
      />
      <Metric label={copy.location} value={plan.geography_name} />
      <Metric label={copy.areaHectares} value={`${formatArea(plan.area_ha, language)} ${copy.areaUnit}`} />
      <Metric label={copy.plantingDate} value={formatDate(plan.planting_date, language)} />
      <Metric
        label={copy.harvestPeriod}
        value={formatPeriod(plan.harvest_start, plan.harvest_end, language)}
      />
      <Metric label={copy.status} value={planStatusLabel(plan.status, language)} />
    </dl>
  );
}

function FarmerDashboard(props: PageProps) {
  const { language } = props;
  const copy = phase5Messages[language];
  const [plans, setPlans] = useState<PlantingPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadPlans() {
    setLoading(true);
    setError(null);
    try {
      setPlans(await apiRequest<PlantingPlan[]>("/plans"));
    } catch (caught) {
      setError(errorMessage(caught, language));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadPlans();
  }, []);

  const today = new Date().toISOString().slice(0, 10);
  const activePlans = plans.filter((plan) => plan.status === "active");
  const upcoming = activePlans
    .filter((plan) => plan.harvest_end >= today)
    .sort((first, second) => first.harvest_start.localeCompare(second.harvest_start))
    .slice(0, 3);
  const recent = [...plans]
    .sort((first, second) => second.planting_date.localeCompare(first.planting_date))
    .slice(0, 3);

  return (
    <PageFrame {...props}>
      <div className="platform-page stack">
        <section className="page-heading">
          <p className="eyebrow">{copy.roleFarmer}</p>
          <h1>{copy.welcomeFarmer}, {props.user.display_name}</h1>
          <p>{copy.dashboardFarmerBody}</p>
          <div className="button-row">
            <InternalLink className="primary-button" href="/plans/new">{copy.addPlan}</InternalLink>
            <InternalLink className="secondary-button" href="/plans">{copy.viewPlans}</InternalLink>
          </div>
        </section>

        {loading ? <p aria-live="polite">{copy.loading}</p> : null}
        {error ? (
          <div className="notice-error" role="alert">
            <p>{error}</p>
            <button className="secondary-button" type="button" onClick={() => void loadPlans()}>
              {copy.retry}
            </button>
          </div>
        ) : null}
        {!loading && !error ? (
          <>
            <dl className="metric-grid">
              <Metric label={copy.activePlans} value={activePlans.length} />
              <Metric label={copy.upcomingHarvests} value={upcoming.length} />
            </dl>
            <section className="content-card stack" aria-labelledby="upcoming-title">
              <h2 id="upcoming-title">{copy.upcomingHarvests}</h2>
              {upcoming.length === 0 ? <p>{copy.noUpcomingHarvests}</p> : (
                <ul className="simple-list">
                  {upcoming.map((plan) => (
                    <li key={plan.plan_id}>
                      <InternalLink href={`/plans/${plan.plan_id}`}>
                        {localizedCropName(language, plan.crop_name_en, plan.crop_name_tl)}
                      </InternalLink>
                      <span>{formatPeriod(plan.harvest_start, plan.harvest_end, language)}</span>
                      <span className="table-actions">
                        <InternalLink href={`/prices?crop_id=${encodeURIComponent(plan.crop_id)}`}>{copy.navPrices}</InternalLink>
                        <InternalLink href={`/map?crop_id=${encodeURIComponent(plan.crop_id)}`}>{copy.navMap}</InternalLink>
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
            <section className="content-card stack" aria-labelledby="recent-title">
              <div className="split-heading">
                <h2 id="recent-title">{copy.recentPlans}</h2>
                <InternalLink href="/plans">{copy.viewPlans}</InternalLink>
              </div>
              {recent.length === 0 ? <p>{copy.noRecentPlans}</p> : (
                <ul className="simple-list">
                  {recent.map((plan) => (
                    <li key={plan.plan_id}>
                      <InternalLink href={`/plans/${plan.plan_id}`}>
                        {localizedCropName(language, plan.crop_name_en, plan.crop_name_tl)}
                      </InternalLink>
                      <span>{plan.geography_name}</span>
                      <span className="table-actions">
                        <InternalLink href={`/prices?crop_id=${encodeURIComponent(plan.crop_id)}`}>{copy.navPrices}</InternalLink>
                        <InternalLink href={`/map?crop_id=${encodeURIComponent(plan.crop_id)}`}>{copy.navMap}</InternalLink>
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        ) : null}
        <section className="content-card stack" aria-labelledby="explore-heading">
          <h2 id="explore-heading">{copy.exploreTools}</h2>
          <p>{copy.exploreBody}</p>
          <div className="button-row">
            <InternalLink className="secondary-button" href="/explore">{copy.navExplore}</InternalLink>
            <InternalLink className="quiet-button" href="/demo?replay=1">{copy.replayDemo}</InternalLink>
          </div>
        </section>
      </div>
    </PageFrame>
  );
}

function CooperativeDashboard(props: PageProps) {
  const { language } = props;
  const copy = phase5Messages[language];
  const [overview, setOverview] = useState<CooperativeOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadOverview() {
    setLoading(true);
    setError(null);
    try {
      setOverview(await apiRequest<CooperativeOverview>("/cooperative/overview"));
    } catch (caught) {
      setError(errorMessage(caught, language));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadOverview();
  }, []);

  const cropTotals = useMemo(() => {
    const totals = new Map<string, { nameEn: string; nameTl: string | null; area: number; count: number }>();
    for (const item of overview?.aggregates ?? []) {
      const total = totals.get(item.crop_id) ?? {
        nameEn: item.crop_name_en,
        nameTl: item.crop_name_tl,
        area: 0,
        count: 0,
      };
      total.area += item.planned_area_ha;
      total.count += item.plan_count;
      totals.set(item.crop_id, total);
    }
    return [...totals.entries()].sort((first, second) => first[1].nameEn.localeCompare(second[1].nameEn));
  }, [overview]);

  return (
    <PageFrame {...props}>
      <div className="platform-page stack">
        <section className="page-heading">
          <p className="eyebrow">{copy.roleCooperative}</p>
          <h1>{copy.welcomeCooperative}: {overview?.organization_name ?? props.user.display_name}</h1>
          <p>{copy.dashboardCooperativeBody}</p>
        </section>
        {loading ? <p aria-live="polite">{copy.loading}</p> : null}
        {error ? (
          <div className="notice-error" role="alert">
            <p>{error}</p>
            <button className="secondary-button" type="button" onClick={() => void loadOverview()}>
              {copy.retry}
            </button>
          </div>
        ) : null}
        {!loading && !error && overview ? (
          <>
            <dl className="metric-grid">
              <Metric label={copy.totalActivePlans} value={overview.total_active_plan_count} />
              <Metric
                label={copy.totalPlannedArea}
                value={`${formatArea(overview.total_planned_area_ha, language)} ${copy.areaUnit}`}
              />
            </dl>
            <section className="content-card stack" aria-labelledby="crop-totals-title">
              <h2 id="crop-totals-title">{copy.cropTotals}</h2>
              {cropTotals.length === 0 ? <p>{copy.noCooperativePlans}</p> : (
                <div className="responsive-table">
                  <table>
                    <thead><tr><th>{copy.crop}</th><th>{copy.planCount}</th><th>{copy.area}</th></tr></thead>
                    <tbody>
                      {cropTotals.map(([cropId, total]) => (
                        <tr key={cropId}>
                          <td data-label={copy.crop}>{localizedCropName(language, total.nameEn, total.nameTl)}</td>
                          <td data-label={copy.planCount}>{total.count}</td>
                          <td data-label={copy.area}>{formatArea(total.area, language)} {copy.areaUnit}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
            <section className="content-card stack" aria-labelledby="overview-details-title">
              <h2 id="overview-details-title">{copy.overviewDetails}</h2>
              {overview.aggregates.length === 0 ? <p>{copy.noCooperativePlans}</p> : (
                <div className="responsive-table">
                  <table>
                    <thead>
                      <tr>
                        <th>{copy.crop}</th><th>{copy.location}</th><th>{copy.period}</th>
                        <th>{copy.planCount}</th><th>{copy.area}</th><th>{copy.communityRisk}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {overview.aggregates.map((item) => (
                        <CooperativeAggregateRow key={`${item.crop_id}:${item.geography_id}:${item.period_start}`} item={item} language={language} />
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
            <section className="content-card stack">
              <h2>{copy.exploreTools}</h2>
              <p>{copy.exploreBody}</p>
              <InternalLink className="secondary-button" href="/explore">{copy.navExplore}</InternalLink>
            </section>
          </>
        ) : null}
      </div>
    </PageFrame>
  );
}

function CooperativeAggregateRow({ item, language }: { item: CooperativeAggregate; language: Language }) {
  const copy = phase5Messages[language];
  const existingCopy = messages[language].platform;
  const context = item.community_risk;
  const cropName = localizedCropName(language, item.crop_name_en, item.crop_name_tl);
  const ratioText = context.ratio === null
    ? copy.noRiskScore
    : formatArea(context.ratio, language);
  const referenceText = context.reference_area_ha === null
    ? copy.referenceNotReady
    : formatArea(context.reference_area_ha, language);
  const explanation = context.status === "available" && context.risk && context.ratio !== null && context.reference_area_ha !== null
    ? language === "tl"
      ? copy.communityRiskExplanation(
        cropName,
        context.planned_area_ha === null ? copy.noRiskScore : formatArea(context.planned_area_ha, language),
        referenceText,
        ratioText,
        riskLabel(context.risk, language),
      )
      : context.explanation
    : language === "tl"
       ? copy.communityRiskUnavailableExplanation(
         cropName,
         context.planned_area_ha === null ? copy.noRiskScore : formatArea(context.planned_area_ha, language),
       )
      : context.explanation;
  return (
    <tr>
      <td data-label={copy.crop}>{localizedCropName(language, item.crop_name_en, item.crop_name_tl)}</td>
      <td data-label={copy.location}>{item.geography_name}</td>
      <td data-label={copy.period}>{formatPeriod(item.period_start, item.period_end, language)}</td>
      <td data-label={copy.planCount}>{item.plan_count}</td>
      <td data-label={copy.area}>{formatArea(item.planned_area_ha, language)} {copy.areaUnit}</td>
      <td data-label={copy.communityRisk}>
        <strong>
          {context.status === "available" && context.risk
            ? `${riskLabel(context.risk, language)} (${ratioText})`
            : copy.riskNotReady}
        </strong>
        <details className="risk-details">
          <summary>{copy.riskDetails}</summary>
          <p>{explanation}</p>
           <p>{copy.communityRiskInputs(
             context.planned_area_ha === null ? copy.noRiskScore : formatArea(context.planned_area_ha, language),
            referenceText,
            context.contributing_plan_count,
          )}</p>
        </details>
      </td>
    </tr>
  );
}

function PlansPage(props: PageProps) {
  const { language } = props;
  const copy = phase5Messages[language];
  const [plans, setPlans] = useState<PlantingPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<number | null>(null);

  async function loadPlans() {
    setLoading(true);
    setError(null);
    try {
      setPlans(await apiRequest<PlantingPlan[]>("/plans"));
    } catch (caught) {
      setError(errorMessage(caught, language));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadPlans();
    if (new URLSearchParams(window.location.search).get("cancelled") === "1") {
      setSuccess(copy.cancelSuccess);
    }
  }, []);

  async function cancelPlan(planId: number) {
    setError(null);
    try {
      const cancelled = await apiRequest<PlantingPlan>(`/plans/${planId}`, { method: "DELETE" });
      setPlans((current) => current.map((plan) => plan.plan_id === planId ? cancelled : plan));
      setSuccess(copy.cancelSuccess);
      setConfirmId(null);
    } catch (caught) {
      setError(errorMessage(caught, language));
    }
  }

  return (
    <PageFrame {...props}>
      <div className="platform-page stack">
        <section className="page-heading split-heading">
          <div className="stack">
            <h1>{copy.plansTitle}</h1>
            <p>{copy.plansIntro}</p>
          </div>
          <InternalLink className="primary-button" href="/plans/new">{copy.addPlan}</InternalLink>
        </section>
        {success ? <p className="notice-success" role="status">{success}</p> : null}
        {error ? <div className="notice-error" role="alert"><p>{error}</p></div> : null}
        {loading ? <p aria-live="polite">{copy.loading}</p> : null}
        {!loading && !error && plans.length === 0 ? (
          <section className="content-card stack">
            <h2>{copy.plansEmptyTitle}</h2>
            <p>{copy.plansEmptyBody}</p>
            <InternalLink className="primary-button" href="/plans/new">{copy.addPlan}</InternalLink>
          </section>
        ) : null}
        {!loading && !error && plans.length > 0 ? (
          <div className="responsive-table">
            <table>
              <thead>
                <tr>
                  <th>{copy.crop}</th><th>{copy.location}</th><th>{copy.area}</th>
                  <th>{copy.plantingDate}</th><th>{copy.harvestPeriod}</th><th>{copy.status}</th><th>{copy.actions}</th>
                </tr>
              </thead>
              <tbody>
                {plans.map((plan) => (
                  <tr key={plan.plan_id}>
                    <td data-label={copy.crop}>{localizedCropName(language, plan.crop_name_en, plan.crop_name_tl)}</td>
                    <td data-label={copy.location}>{plan.geography_name}</td>
                    <td data-label={copy.area}>{formatArea(plan.area_ha, language)} {copy.areaUnit}</td>
                    <td data-label={copy.plantingDate}>{formatDate(plan.planting_date, language)}</td>
                    <td data-label={copy.harvestPeriod}>{formatPeriod(plan.harvest_start, plan.harvest_end, language)}</td>
                    <td data-label={copy.status}>{planStatusLabel(plan.status, language)}</td>
                    <td data-label={copy.actions}>
                      <div className="table-actions">
                        <InternalLink href={`/plans/${plan.plan_id}`}>{copy.view}</InternalLink>
                        {plan.status === "active" ? (
                          <>
                            <InternalLink href={`/plans/${plan.plan_id}/edit`}>{copy.edit}</InternalLink>
                            <button className="quiet-button" type="button" onClick={() => setConfirmId(plan.plan_id)}>
                              {copy.cancelPlan}
                            </button>
                          </>
                        ) : null}
                      </div>
                      {confirmId === plan.plan_id ? (
                        <div className="inline-confirm" role="group" aria-label={copy.confirmCancelTitle}>
                          <p>{copy.confirmCancelBody}</p>
                          <button className="secondary-button" type="button" onClick={() => void cancelPlan(plan.plan_id)}>
                            {copy.confirmCancel}
                          </button>
                          <button className="quiet-button" type="button" onClick={() => setConfirmId(null)}>
                            {copy.keepPlan}
                          </button>
                        </div>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </PageFrame>
  );
}

function PlanDetailsPage({ planId, ...props }: PageProps & { planId: number }) {
  const { language } = props;
  const copy = phase5Messages[language];
  const [plan, setPlan] = useState<PlantingPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [confirmCancel, setConfirmCancel] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  async function loadPlan() {
    setLoading(true);
    setError(null);
    try {
      setPlan(await apiRequest<PlantingPlan>(`/plans/${planId}`));
    } catch (caught) {
      setError(errorMessage(caught, language));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadPlan();
    if (new URLSearchParams(window.location.search).get("saved") === "1") {
      setSuccess(copy.saveSuccess);
    }
  }, [planId]);

  async function cancelPlan() {
    setError(null);
    try {
      const cancelled = await apiRequest<PlantingPlan>(`/plans/${planId}`, { method: "DELETE" });
      setPlan(cancelled);
      setSuccess(copy.cancelSuccess);
      setConfirmCancel(false);
    } catch (caught) {
      setError(errorMessage(caught, language));
    }
  }

  return (
    <PageFrame {...props}>
      <div className="platform-page stack">
        <InternalLink href="/plans">{copy.backToPlans}</InternalLink>
        {loading ? <p aria-live="polite">{copy.loading}</p> : null}
        {error ? (
          <div className="notice-error" role="alert">
            <p>{error}</p>
            <button className="secondary-button" type="button" onClick={() => void loadPlan()}>{copy.retry}</button>
          </div>
        ) : null}
        {success ? <p className="notice-success" role="status">{success}</p> : null}
        {plan ? (
          <section className="content-card stack" aria-labelledby="plan-details-title">
            <div className="split-heading">
              <div className="stack">
                <p className="eyebrow">{copy.planDetails}</p>
                <h1 id="plan-details-title">
                  {localizedCropName(language, plan.crop_name_en, plan.crop_name_tl)}
                </h1>
              </div>
              <span className="status-label">{planStatusLabel(plan.status, language)}</span>
            </div>
            <PlanSummary plan={plan} language={language} />
            <p className="muted-text">{copy.planFormHint}</p>
            {plan.status === "active" ? (
              <div className="button-row">
                <InternalLink className="primary-button" href={`/plans/${plan.plan_id}/edit`}>
                  {copy.edit}
                </InternalLink>
                <button className="secondary-button" type="button" onClick={() => setConfirmCancel(true)}>
                  {copy.cancelPlan}
                </button>
              </div>
            ) : null}
            {confirmCancel ? (
              <div className="inline-confirm" role="group" aria-label={copy.confirmCancelTitle}>
                <h2>{copy.confirmCancelTitle}</h2>
                <p>{copy.confirmCancelBody}</p>
                <div className="button-row">
                  <button className="secondary-button" type="button" onClick={() => void cancelPlan()}>
                    {copy.confirmCancel}
                  </button>
                  <button className="quiet-button" type="button" onClick={() => setConfirmCancel(false)}>
                    {copy.keepPlan}
                  </button>
                </div>
              </div>
            ) : null}
          </section>
        ) : null}
      </div>
    </PageFrame>
  );
}

function formFingerprint(values: PlanFormValues): string {
  return JSON.stringify({
    crop_id: values.crop_id,
    region_id: values.region_id,
    province_id: values.province_id,
    geography_id: values.geography_id,
    area_ha: values.area_ha,
    planting_date: values.planting_date,
    period_key: values.period_key,
    comparison_crop_ids: [...values.comparison_crop_ids].sort(),
  });
}

function riskFingerprint(values: PlanFormValues): string {
  return JSON.stringify({
    crop_id: values.crop_id,
    geography_id: values.geography_id,
    area_ha: Number(values.area_ha),
    period_key: values.period_key,
    comparison_crop_ids: [...values.comparison_crop_ids].sort(),
  });
}

function periodKey(period: PlanningPeriod): string {
  return `${period.period_start}|${period.period_end}`;
}

function RiskPreview({
  result,
  crops,
  language,
}: {
  result: RiskCheckResponse;
  crops: CropLookup[];
  language: Language;
}) {
  const copy = phase5Messages[language];
  const existingCopy = messages[language].platform;
  const labelForCrop = (cropId: string) => {
    const crop = crops.find((item) => item.crop_id === cropId);
    return crop
      ? localizedCropName(language, crop.canonical_name_en, crop.canonical_name_tl)
      : cropId;
  };
  const number = (value: number | null) => value === null ? copy.noRiskScore : formatArea(value, language);
  const risk = (value: RiskLevel | null) => value ? riskLabel(value, language) : copy.noRiskScore;
  const areaText = (value: number | null) => value === null ? copy.noRiskScore : formatArea(value, language);
  const explanation = result.status === "available" && result.risk
    ? language === "tl"
      ? existingCopy.explanation(
        labelForCrop(result.crop_id),
         areaText(result.existing_planned_area_ha),
        formatArea(result.proposed_area_ha, language),
         areaText(result.projected_planned_area_ha),
        result.reference_area_ha === null
          ? copy.referenceNotReady
          : formatArea(result.reference_area_ha, language),
        result.ratio === null ? copy.noRiskScore : formatArea(result.ratio, language),
        risk(result.risk),
      )
      : result.explanation
    : language === "tl"
      ? copy.unavailableRiskExplanation(
        labelForCrop(result.crop_id),
         areaText(result.existing_planned_area_ha),
        formatArea(result.proposed_area_ha, language),
         areaText(result.projected_planned_area_ha),
      )
      : result.explanation;

  return (
    <section className="content-card stack" aria-labelledby="risk-preview-title">
      <h2 id="risk-preview-title">{copy.previewTitle}</h2>
      {result.status === "available" && result.risk ? (
        <dl className="metric-grid">
          <Metric label={copy.risk} value={risk(result.risk)} />
          <Metric label={copy.ratio} value={result.ratio?.toFixed(2) ?? copy.noRiskScore} />
          <Metric
            label={copy.existingArea}
             value={result.existing_planned_area_ha === null
               ? copy.noRiskScore
               : `${formatArea(result.existing_planned_area_ha, language)} ${copy.areaUnit}`}
          />
          <Metric
            label={copy.proposedArea}
            value={`${formatArea(result.proposed_area_ha, language)} ${copy.areaUnit}`}
          />
          <Metric
            label={copy.projectedArea}
             value={result.projected_planned_area_ha === null
               ? copy.noRiskScore
               : `${formatArea(result.projected_planned_area_ha, language)} ${copy.areaUnit}`}
          />
          <Metric
            label={copy.referenceArea}
            value={result.reference_area_ha === null
              ? copy.noRiskScore
              : `${formatArea(result.reference_area_ha, language)} ${copy.areaUnit}`}
          />
          <Metric label={copy.contributingPlans} value={result.contributing_plan_count} />
        </dl>
      ) : (
        <p className="notice-warning">{copy.noRiskScore}</p>
      )}
      <div className="stack">
        <h3>{copy.explanation}</h3>
        <p>{explanation}</p>
      </div>
      {result.comparisons.length > 0 ? (
        <section className="stack" aria-labelledby="comparison-results-title">
          <h3 id="comparison-results-title">{copy.comparisonResults}</h3>
          <div className="responsive-table">
            <table>
              <thead>
                <tr><th>{copy.crop}</th><th>{copy.currentPressure}</th><th>{copy.withYourPlan}</th></tr>
              </thead>
              <tbody>
                {result.comparisons.map((comparison) => (
                  <tr key={comparison.crop_id}>
                    <td data-label={copy.crop}>{labelForCrop(comparison.crop_id)}</td>
                    <td data-label={copy.currentPressure}>
                      {number(comparison.current_ratio)} · {risk(comparison.current_risk)}
                    </td>
                    <td data-label={copy.withYourPlan}>
                      {number(comparison.projected_ratio_if_same_area)} · {risk(comparison.projected_risk_if_same_area)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="muted-text">{existingCopy.collectiveBody}</p>
        </section>
      ) : null}
    </section>
  );
}

function asLookupList<T>(payload: T[] | { items: T[] }): T[] {
  return Array.isArray(payload) ? payload : payload.items;
}

function PlanFormPage({ planId, ...props }: PageProps & { planId?: number }) {
  const { language } = props;
  const copy = phase5Messages[language];
  const [crops, setCrops] = useState<CropLookup[]>([]);
  const [geographies, setGeographies] = useState<GeographyLookup[]>([]);
  const [periods, setPeriods] = useState<PlanningPeriod[]>([]);
  const [form, setForm] = useState<PlanFormValues>(emptyPlanForm);
  const formRef = useRef(form);
  formRef.current = form;
  const [initialForm, setInitialForm] = useState<PlanFormValues | null>(null);
  const [preview, setPreview] = useState<{ fingerprint: string; result: RiskCheckResponse } | null>(null);
  const [previewStale, setPreviewStale] = useState(false);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [comparisonSearch, setComparisonSearch] = useState("");
  const [showAllComparisons, setShowAllComparisons] = useState(false);

  async function loadForm() {
    setLoading(true);
    setLoadError(null);
    try {
      const [cropResponse, geographyResponse, periodItems] = await Promise.all([
        apiRequest<CropListResponse | CropLookup[]>("/crops"),
        apiRequest<GeographyLookup[] | { items: GeographyLookup[] }>("/geographies"),
        apiRequest<PlanningPeriod[]>("/planning-periods"),
      ]);
      const cropItems = asLookupList<CropLookup>(cropResponse);
      const geographyItems = asLookupList<GeographyLookup>(geographyResponse);
      setCrops(cropItems);
      setGeographies(geographyItems);
      setPeriods(periodItems);
      if (planId !== undefined) {
        const plan = await apiRequest<PlantingPlan>(`/plans/${planId}`);
        const selectedGeography = geographyItems.find(
          (item) => item.geography_id === plan.geography_id,
        );
        const selectedProvince = geographyItems.find(
          (item) => item.geography_id === selectedGeography?.parent_geography_id,
        );
        const selectedPeriod = periodItems.find((item) =>
          item.period_start <= plan.harvest_start && item.period_end >= plan.harvest_end,
        );
        if (!selectedPeriod) {
          throw new ApiClientError("UNSUPPORTED_HARVEST_PERIOD", "Unsupported plan period.", 400);
        }
        const nextForm: PlanFormValues = {
          crop_id: plan.crop_id,
          region_id: selectedProvince?.parent_geography_id ?? "",
          province_id: selectedGeography?.parent_geography_id ?? "",
          geography_id: plan.geography_id,
          area_ha: String(plan.area_ha),
          planting_date: plan.planting_date,
          period_key: periodKey(selectedPeriod),
          comparison_crop_ids: [],
        };
        setForm(nextForm);
        formRef.current = nextForm;
        setInitialForm(nextForm);
      }
    } catch (caught) {
      setLoadError(errorMessage(caught, language));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadForm();
  }, [planId]);

  const regions = geographies.filter((geography) => geography.level === "region");
  const selectedRegionId = form.region_id;
  const selectedProvinceId = form.province_id;
  const provinces = geographies.filter(
    (geography) => geography.level === "province" && geography.parent_geography_id === selectedRegionId,
  );
  const municipalities = geographies.filter(
    (geography) => geography.level === "municipality_city" && geography.parent_geography_id === selectedProvinceId,
  );
  const selectedPeriod = periods.find((period) => periodKey(period) === form.period_key);
  const fingerprint = formFingerprint(form);
  const isPreviewFresh = preview?.fingerprint === fingerprint;
  const requiresPreview = planId === undefined
    || (initialForm !== null && riskFingerprint(form) !== riskFingerprint(initialForm));
  const canSave = !saving && (!requiresPreview || isPreviewFresh);

  function updateField<Key extends keyof PlanFormValues>(key: Key, value: PlanFormValues[Key]) {
    if (preview) setPreviewStale(true);
    setPreview(null);
    setError(null);
    setForm((current) => ({ ...current, [key]: value }));
  }

  function toggleComparison(cropId: string) {
    const next = form.comparison_crop_ids.includes(cropId)
      ? form.comparison_crop_ids.filter((selected) => selected !== cropId)
      : [...form.comparison_crop_ids, cropId].slice(0, 5);
    updateField("comparison_crop_ids", next);
  }

  async function checkRisk() {
    if (!selectedPeriod || !form.crop_id || !form.geography_id || !form.planting_date || !form.area_ha) {
      setError(copy.previewRequired);
      return;
    }
    const area = Number(form.area_ha);
    if (!Number.isFinite(area) || area <= 0) {
      setError(copy.errors.INVALID_AREA);
      return;
    }
    const snapshot = formFingerprint(form);
    setChecking(true);
    setError(null);
    try {
      const result = await apiRequest<RiskCheckResponse>("/risk/check", {
        method: "POST",
        body: {
          crop_id: form.crop_id,
          geography_id: form.geography_id,
          proposed_area_ha: area,
          harvest_start: selectedPeriod.period_start,
          harvest_end: selectedPeriod.period_end,
          comparison_crop_ids: form.comparison_crop_ids,
        },
      });
      if (formFingerprint(formRef.current) !== snapshot) {
        setPreview(null);
        setPreviewStale(true);
        return;
      }
      setPreview({ fingerprint: snapshot, result });
      setPreviewStale(false);
    } catch (caught) {
      setError(errorMessage(caught, language));
    } finally {
      setChecking(false);
    }
  }

  async function savePlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPeriod) {
      setError(copy.errors.INVALID_REQUEST);
      return;
    }
    if (requiresPreview && !isPreviewFresh) {
      setError(copy.previewRequired);
      return;
    }
    setSaving(true);
    setError(null);
    const payload: PlantingPlanInput = {
      crop_id: form.crop_id,
      geography_id: form.geography_id,
      area_ha: Number(form.area_ha),
      planting_date: form.planting_date,
      harvest_start: selectedPeriod.period_start,
      harvest_end: selectedPeriod.period_end,
    };
    try {
      const saved = planId === undefined
        ? await apiRequest<PlantingPlan>("/plans", { method: "POST", body: payload })
        : await apiRequest<PlantingPlan>(`/plans/${planId}`, { method: "PATCH", body: payload });
      navigate(`/plans/${saved.plan_id}?saved=1`);
    } catch (caught) {
      setError(errorMessage(caught, language));
      setSaving(false);
    }
  }

  return (
    <PageFrame {...props}>
      <div className="platform-page stack">
        <InternalLink href="/plans">{copy.backToPlans}</InternalLink>
        <section className="page-heading">
          <h1>{planId === undefined ? copy.newPlanTitle : copy.editPlanTitle}</h1>
          <p>{copy.planFormHint}</p>
        </section>
        {loading ? <p aria-live="polite">{copy.loading}</p> : null}
        {loadError ? (
          <div className="notice-error" role="alert">
            <p>{loadError}</p>
            <button className="secondary-button" type="button" onClick={() => void loadForm()}>{copy.retry}</button>
          </div>
        ) : null}
        {error ? <p className="notice-error" role="alert">{error}</p> : null}
        {!loading && !loadError ? (
          <form className="content-card stack" onSubmit={(event) => void savePlan(event)}>
            <div className="form-grid">
              <label>
                <span>{copy.crop}</span>
                <select
                  required
                  value={form.crop_id}
                  onChange={(event) => updateField("crop_id", event.target.value)}
                >
                  <option value="">{copy.chooseCrop}</option>
                  {crops.map((crop) => (
                    <option key={crop.crop_id} value={crop.crop_id}>
                      {localizedCropName(language, crop.canonical_name_en, crop.canonical_name_tl)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>{copy.region}</span>
                <select
                  required
                  value={selectedRegionId}
                  onChange={(event) => {
                    updateField("region_id", event.target.value);
                    updateField("province_id", "");
                    updateField("geography_id", "");
                  }}
                >
                  <option value="">{copy.chooseRegion}</option>
                  {regions.map((region) => <option key={region.geography_id} value={region.geography_id}>{region.name}</option>)}
                </select>
              </label>
              <label>
                <span>{copy.province}</span>
                <select
                  required
                  disabled={!selectedRegionId}
                  value={selectedProvinceId}
                  onChange={(event) => {
                    updateField("province_id", event.target.value);
                    updateField("geography_id", "");
                  }}
                >
                  <option value="">{copy.chooseProvince}</option>
                  {provinces.map((province) => <option key={province.geography_id} value={province.geography_id}>{province.name}</option>)}
                </select>
              </label>
              <label>
                <span>{copy.municipality}</span>
                <select
                  required
                  disabled={!selectedProvinceId}
                  value={form.geography_id}
                  onChange={(event) => updateField("geography_id", event.target.value)}
                >
                  <option value="">{copy.chooseCity}</option>
                  {municipalities.map((municipality) => (
                    <option key={municipality.geography_id} value={municipality.geography_id}>
                      {municipality.name}
                    </option>
                  ))}
                </select>
              </label>
              <div className="stack form-field">
                <label htmlFor="plan-area">{copy.areaHectares}</label>
                <input
                  id="plan-area"
                  aria-describedby="plan-area-help"
                  required
                  min="0.0001"
                  step="0.0001"
                  type="number"
                  value={form.area_ha}
                  onChange={(event) => updateField("area_ha", event.target.value)}
                />
                <small id="plan-area-help">{copy.areaHelp}</small>
              </div>
              <label>
                <span>{copy.plantingDate}</span>
                <input
                  required
                  type="date"
                  value={form.planting_date}
                  onChange={(event) => updateField("planting_date", event.target.value)}
                />
              </label>
              <label>
                <span>{copy.harvestPeriod}</span>
                <select
                  required
                  value={form.period_key}
                  onChange={(event) => updateField("period_key", event.target.value)}
                >
                  <option value="">{copy.choosePeriod}</option>
                  {periods.map((period) => (
                    <option key={periodKey(period)} value={periodKey(period)}>
                      {formatPeriod(period.period_start, period.period_end, language)}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <fieldset className="comparison-fieldset">
              <legend>{copy.comparisons}</legend>
              <p>{copy.comparisonHelp}</p>
              <label>
                <span>{copy.comparisonSearch}</span>
                <input
                  type="search"
                  value={comparisonSearch}
                  onChange={(event) => setComparisonSearch(event.target.value)}
                  placeholder={copy.comparisonSearch}
                />
              </label>
              <div className="comparison-options">
                {(() => {
                  const query = comparisonSearch.trim().toLowerCase();
                  const pool = crops.filter((crop) => crop.crop_id !== form.crop_id).filter((crop) => {
                    if (!query) return true;
                    const name = localizedCropName(language, crop.canonical_name_en, crop.canonical_name_tl).toLowerCase();
                    return name.includes(query) || crop.crop_id.toLowerCase().includes(query);
                  });
                  const selected = pool.filter((crop) => form.comparison_crop_ids.includes(crop.crop_id));
                  const unselected = pool.filter((crop) => !form.comparison_crop_ids.includes(crop.crop_id));
                  const visible = showAllComparisons ? [...selected, ...unselected] : [...selected, ...unselected.slice(0, Math.max(0, 4 - selected.length))];
                  return visible.map((crop) => (
                    <label className="checkbox-row" key={crop.crop_id}>
                      <input
                        type="checkbox"
                        checked={form.comparison_crop_ids.includes(crop.crop_id)}
                        disabled={!form.comparison_crop_ids.includes(crop.crop_id) && form.comparison_crop_ids.length >= 5}
                        onChange={() => toggleComparison(crop.crop_id)}
                      />
                      <span>{localizedCropName(language, crop.canonical_name_en, crop.canonical_name_tl)}</span>
                    </label>
                  ));
                })()}
              </div>
              <button className="quiet-button" type="button" onClick={() => setShowAllComparisons((open) => !open)}>
                {showAllComparisons ? copy.showFewerComparisons : copy.showAllComparisons}
              </button>
            </fieldset>

            <p className="muted-text">{copy.checkStepsHint}</p>
            <div className="button-row">
              <button className="primary-button" disabled={checking || saving} type="button" onClick={() => void checkRisk()}>
                {checking ? copy.checkingRisk : copy.checkRisk}
              </button>
              <button className="secondary-button" disabled={!canSave || checking} type="submit">
                {saving ? copy.savingPlan : copy.savePlan}
              </button>
              <button className="quiet-button" type="button" onClick={() => navigate("/plans")}>
                {copy.keepPlan}
              </button>
            </div>
            {previewStale ? <p className="notice-warning" role="status">{copy.previewStale}</p> : null}
            {requiresPreview && !isPreviewFresh ? <p className="muted-text">{copy.previewRequired}</p> : null}
          </form>
        ) : null}
        {isPreviewFresh && preview ? (
          <RiskPreview result={preview.result} crops={crops} language={language} />
        ) : null}
      </div>
    </PageFrame>
  );
}

export function SettingsPage(props: PageProps) {
  const { language, user } = props;
  const copy = phase5Messages[language];
  const [membership, setMembership] = useState<AccountMembershipResponse["membership"]>(null);
  const [membershipLoading, setMembershipLoading] = useState(true);
  const [joinCode, setJoinCode] = useState("");
  const [membershipError, setMembershipError] = useState<string | null>(null);
  const [joining, setJoining] = useState(false);

  async function loadMembership() {
    setMembershipLoading(true);
    setMembershipError(null);
    try {
      const result = await apiRequest<AccountMembershipResponse>("/account/membership");
      setMembership(result.membership);
    } catch (caught) {
      setMembershipError(errorMessage(caught, language));
    } finally {
      setMembershipLoading(false);
    }
  }

  useEffect(() => {
    void loadMembership();
  }, []);

  async function joinCooperative(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setJoining(true);
    setMembershipError(null);
    try {
      const result = await apiRequest<AccountMembershipResponse>("/account/membership", {
        method: "POST",
        body: { join_code: joinCode },
      });
      setMembership(result.membership);
      setJoinCode("");
    } catch (caught) {
      setMembershipError(errorMessage(caught, language));
    } finally {
      setJoining(false);
    }
  }

  return (
    <PageFrame {...props}>
      <div className="platform-page stack">
        <section className="page-heading">
          <h1>{copy.settingsTitle}</h1>
          <p>{copy.settingsIntro}</p>
        </section>
        <section className="content-card stack" aria-label={copy.settingsTitle}>
          <dl className="plan-summary">
            <Metric label={copy.accountName} value={user.display_name} />
            <Metric label={copy.accountEmail} value={user.email} />
            <Metric
              label={copy.accountRole}
              value={user.role === "cooperative" ? copy.roleCooperative : copy.roleFarmer}
            />
            <Metric
              label={copy.language}
              value={language === "tl" ? messages[language].languageOptions.tl : messages[language].languageOptions.en}
            />
          </dl>
          <label className="settings-language">
            <span>{copy.language}</span>
            <select value={language} onChange={(event) => props.onLanguageChange(event.target.value as Language)}>
              <option value="en">{messages[language].languageOptions.en}</option>
              <option value="tl">{messages[language].languageOptions.tl}</option>
            </select>
          </label>
          <section className="stack" aria-labelledby="membership-title">
            <h2 id="membership-title">{copy.membershipTitle}</h2>
            {membershipLoading ? <p aria-live="polite">{copy.loading}</p> : null}
            {membershipError ? <p className="notice-error" role="alert">{membershipError}</p> : null}
            {!membershipLoading && membership ? (
              <dl className="plan-summary">
                <Metric label={copy.cooperativeName} value={membership.organization_name} />
                <Metric label={copy.cooperativeJoinCode} value={membership.join_code} />
              </dl>
            ) : null}
            {!membershipLoading && !membership && user.role === "farmer" ? (
              <form className="stack" onSubmit={(event) => void joinCooperative(event)}>
                <label>
                  <span>{copy.cooperativeJoinCode}</span>
                  <input
                    required
                    value={joinCode}
                    onChange={(event) => setJoinCode(event.target.value.toUpperCase())}
                    placeholder="TANIM-AB12CD"
                  />
                </label>
                <button className="secondary-button" disabled={joining} type="submit">
                  {joining ? copy.loading : copy.joinCooperative}
                </button>
              </form>
            ) : null}
          </section>
          <div className="button-row">
            <InternalLink className="secondary-button" href="/demo?replay=1">{copy.replayDemo}</InternalLink>
            <a className="quiet-button" href={frontendUrls.docs} target="_blank" rel="noreferrer">{copy.navHelp}</a>
          </div>
        </section>
      </div>
    </PageFrame>
  );
}

export function ExplorePage(props: PageProps) {
  const { language } = props;
  const copy = phase5Messages[language];
  return (
    <PageFrame {...props}>
      <section className="content-card stack">
        <h1>{copy.exploreTitle}</h1>
        <p>{copy.exploreBody}</p>
        <ul className="simple-list">
          <li><InternalLink href="/crops">{copy.navCrops}</InternalLink></li>
          <li><InternalLink href="/prices">{copy.navPrices}</InternalLink></li>
          <li><InternalLink href="/suitability">{copy.navSuitability}</InternalLink></li>
          <li><InternalLink href="/map">{copy.navMap}</InternalLink></li>
          <li><InternalLink href="/weather">{copy.navWeather}</InternalLink></li>
        </ul>
        <InternalLink className="secondary-button" href="/dashboard">{copy.navDashboard}</InternalLink>
      </section>
    </PageFrame>
  );
}

export function PlatformPage({
  path,
  ...props
}: PageProps & { path: string }) {
  const phase6Route = Phase6UtilityRoutes({ path, language: props.language });
  if (phase6Route) {
    return <PageFrame {...props}>{phase6Route}</PageFrame>;
  }
  if (path === "/plans") return <PlansPage {...props} />;
  if (path === "/plans/new") return <PlanFormPage {...props} />;
  if (/^\/plans\/\d+\/edit$/.test(path)) {
    const planId = Number(path.split("/")[2]);
    return <PlanFormPage {...props} planId={planId} />;
  }
  if (/^\/plans\/\d+$/.test(path)) {
    const planId = Number(path.split("/")[2]);
    return <PlanDetailsPage {...props} planId={planId} />;
  }
  if (path === "/settings") return <SettingsPage {...props} />;
  if (path === "/explore") return <ExplorePage {...props} />;
  if (props.user.role === "cooperative") return <CooperativeDashboard {...props} />;
  return <FarmerDashboard {...props} />;
}
