import type { AppSurface, Language } from "@tanim/types";

type Messages = {
  titles: Record<AppSurface, string>;
  description: string;
  languageLabel: string;
  languageOptions: { en: string; tl: string };
  auth: {
    privacyTitle: string;
    privacyIntro: string;
    privacyNeedsAccount: string;
    privacyStoresPlans: string;
    privacyRequiredLabel: string;
    privacyOptionalLabel: string;
    privacyNoticeLink: string;
    privacyNoticeBody: string;
    continueButton: string;
    registerTitle: string;
    nameLabel: string;
    emailLabel: string;
    passwordLabel: string;
    passwordHint: string;
    roleLabel: string;
    farmerOption: string;
    cooperativeOption: string;
    organizationLabel: string;
    organizationHint: string;
    createAccount: string;
    haveAccount: string;
    loginLink: string;
    loginTitle: string;
    loginButton: string;
    noAccount: string;
    registerLink: string;
    requiredField: string;
    privacyError: string;
    formError: string;
    signedIn: string;
    goToTanim: string;
  };
  platform: {
    loading: string;
    demoTitle: string;
    stepLabel: string;
    welcomeTitle: string;
    welcomeBody: string;
    sampleTitle: string;
    sampleBody: string;
    communityTitle: string;
    riskTitle: string;
    comparisonTitle: string;
    collectiveTitle: string;
    finishTitle: string;
    finishBody: string;
    nextButton: string;
    backButton: string;
    startButton: string;
    homeTitle: string;
    homeBody: string;
    replayButton: string;
    logoutButton: string;
    areaUnit: string;
    existingLabel: string;
    proposedLabel: string;
    projectedLabel: string;
    referenceLabel: string;
    ratioLabel: string;
    currentPressureLabel: string;
    hypotheticalPressureLabel: string;
    periodLabel: string;
    locationLabel: string;
    periodSeparator: string;
    collectiveBody: string;
    demoError: string;
    retryButton: string;
    explanation: (
      crop: string,
      existing: string,
      proposed: string,
      projected: string,
      reference: string,
      ratio: string,
      risk: string,
    ) => string;
  };
  riskLabels: Record<"low" | "moderate" | "high", string>;
  errors: Record<string, string>;
};

export const messages: Record<Language, Messages> = {
  en: {
    titles: {
      landing: "TANIM landing page",
      auth: "TANIM sign in and registration",
      platform: "TANIM workspace",
      docs: "TANIM help and documentation",
    },
    description: "TANIM helps farmers plan crops with their community. This is a starter page.",
    languageLabel: "Language / Wika",
    languageOptions: { en: "English", tl: "Tagalog" },
    auth: {
      privacyTitle: "Privacy before registration",
      privacyIntro: "Please read this short notice before you create a TANIM account.",
      privacyNeedsAccount: "TANIM needs your name, email, and role to provide the service.",
      privacyStoresPlans: "When you use TANIM, it will store planting-related information that you enter.",
      privacyRequiredLabel: "I have read the Privacy Notice and agree to the information needed for TANIM.",
      privacyOptionalLabel: "Allow my anonymous data to help improve TANIM.",
      privacyNoticeLink: "Show the Privacy Notice",
      privacyNoticeBody: "TANIM uses account information to provide the service. Your optional improvement choice is separate and is not required.",
      continueButton: "Continue to registration",
      registerTitle: "Create your TANIM account",
      nameLabel: "Name",
      emailLabel: "Email",
      passwordLabel: "Password",
      passwordHint: "Use at least 8 characters.",
      roleLabel: "Role",
      farmerOption: "Farmer",
      cooperativeOption: "Cooperative",
      organizationLabel: "Organization name (optional)",
      organizationHint: "You may add a cooperative or organization name.",
      createAccount: "Create account",
      haveAccount: "Already have an account?",
      loginLink: "Log in",
      loginTitle: "Log in to TANIM",
      loginButton: "Log in",
      noAccount: "Do not have an account yet?",
      registerLink: "Register",
      requiredField: "This field is required.",
      privacyError: "Accept the required Privacy Notice before continuing.",
      formError: "Please check the form and try again.",
      signedIn: "You are already signed in.",
      goToTanim: "Go to TANIM",
    },
    platform: {
      loading: "Loading TANIM...",
      demoTitle: "Your first TANIM demo",
      stepLabel: "Step",
      welcomeTitle: "Welcome to TANIM",
      welcomeBody: "Before planting, TANIM can show how much of the same crop is already planned for the same harvest period.",
      sampleTitle: "Sample planting plan",
      sampleBody: "This is a sample only. It will not be saved as your plan.",
      communityTitle: "Community context",
      riskTitle: "Risk result",
      comparisonTitle: "Crop comparison",
      collectiveTitle: "Collective view",
      finishTitle: "You are ready to start",
      finishBody: "Your real TANIM data will start empty. The demo did not create a planting plan.",
      nextButton: "Next",
      backButton: "Back",
      startButton: "Start using TANIM",
      homeTitle: "TANIM home",
      homeBody: "This authenticated home is ready for the next platform phase. Your first-time demo is complete.",
      replayButton: "Replay the demo",
      logoutButton: "Log out",
      areaUnit: "ha",
      existingLabel: "Existing planned area",
      proposedLabel: "Your sample plan",
      projectedLabel: "Projected area",
      referenceLabel: "Reference",
      ratioLabel: "Ratio",
      currentPressureLabel: "Current pressure",
      hypotheticalPressureLabel: "If the same area is added",
      periodLabel: "Harvest period",
      locationLabel: "Location",
      periodSeparator: "to",
      collectiveBody: "Cooperatives can later see combined crop plans by crop and harvest period. This screen uses demo-only data.",
      demoError: "TANIM cannot load the demo right now. Check the local API and data seed, then retry.",
      retryButton: "Retry",
      explanation: (crop, existing, proposed, projected, reference, ratio, risk) =>
        `Registered ${crop} plans total ${existing} ha. Adding ${proposed} ha gives ${projected} ha against a ${reference} ha reference. The supply pressure ratio is ${ratio}, which is ${risk}.`,
    },
    riskLabels: { low: "Low", moderate: "Moderate", high: "High" },
    errors: {
      INVALID_EMAIL: "Enter a valid email address.",
      INVALID_PASSWORD: "Use at least 8 characters for your password.",
      INVALID_ROLE: "Choose Farmer or Cooperative.",
      PRIVACY_CONSENT_REQUIRED: "Accept the required Privacy Notice before creating an account.",
      PRIVACY_NOTICE_VERSION_UNSUPPORTED: "The Privacy Notice changed. Open it again and continue.",
      EMAIL_ALREADY_REGISTERED: "This email is already registered. Try logging in.",
      INVALID_CREDENTIALS: "Email or password is incorrect.",
      UNAUTHENTICATED: "Please sign in to continue.",
      CSRF_INVALID: "Refresh the page and try again.",
      DATABASE_UNAVAILABLE: "TANIM cannot connect to the local service. Check PostgreSQL and retry.",
      DATASET_NOT_READY: "TANIM demo data is not ready. Run the data seed step and retry.",
    },
  },
  tl: {
    titles: {
      landing: "Panimulang pahina ng TANIM",
      auth: "Pag-login at pagpaparehistro sa TANIM",
      platform: "Lugar ng trabaho sa TANIM",
      docs: "Tulong at gabay sa TANIM",
    },
    description:
      "Tinutulungan ng TANIM ang mga magsasaka na magplano ng pananim kasama ang komunidad. Panimulang pahina ito.",
    languageLabel: "Wika / Language",
    languageOptions: { en: "English", tl: "Tagalog" },
    auth: {
      privacyTitle: "Privacy bago magparehistro",
      privacyIntro: "Basahin ang maikling paunawang ito bago gumawa ng TANIM account.",
      privacyNeedsAccount: "Kailangan ng TANIM ang iyong pangalan, email, at tungkulin para maibigay ang serbisyo.",
      privacyStoresPlans: "Kapag gumamit ka ng TANIM, itatago nito ang impormasyon ng pagtatanim na ilalagay mo.",
      privacyRequiredLabel: "Nabasa ko ang Privacy Notice at sumasang-ayon ako sa impormasyong kailangan ng TANIM.",
      privacyOptionalLabel: "Payagan ang anonymous na datos ko na makatulong sa pagpapabuti ng TANIM.",
      privacyNoticeLink: "Ipakita ang Privacy Notice",
      privacyNoticeBody: "Gagamitin ng TANIM ang impormasyon ng account para maibigay ang serbisyo. Hiwalay ang opsyonal na pahintulot at hindi ito kailangan.",
      continueButton: "Magpatuloy sa pagpaparehistro",
      registerTitle: "Gumawa ng TANIM account",
      nameLabel: "Pangalan",
      emailLabel: "Email",
      passwordLabel: "Password",
      passwordHint: "Gumamit ng hindi bababa sa 8 character.",
      roleLabel: "Tungkulin",
      farmerOption: "Magsasaka",
      cooperativeOption: "Kooperatiba",
      organizationLabel: "Pangalan ng organisasyon (opsyonal)",
      organizationHint: "Maaari kang maglagay ng pangalan ng kooperatiba o organisasyon.",
      createAccount: "Gumawa ng account",
      haveAccount: "May account ka na?",
      loginLink: "Mag-login",
      loginTitle: "Mag-login sa TANIM",
      loginButton: "Mag-login",
      noAccount: "Wala ka pang account?",
      registerLink: "Magparehistro",
      requiredField: "Kailangan ang field na ito.",
      privacyError: "Tanggapin ang kinakailangang Privacy Notice bago magpatuloy.",
      formError: "Suriin ang form at subukan muli.",
      signedIn: "Naka-login ka na.",
      goToTanim: "Pumunta sa TANIM",
    },
    platform: {
      loading: "Ikinakarga ang TANIM...",
      demoTitle: "Unang demo mo sa TANIM",
      stepLabel: "Hakbang",
      welcomeTitle: "Maligayang pagdating sa TANIM",
      welcomeBody: "Bago magtanim, maaaring ipakita ng TANIM kung gaano karami ng parehong pananim ang nakaplano para sa parehong panahon ng ani.",
      sampleTitle: "Halimbawang plano ng pagtatanim",
      sampleBody: "Halimbawa lamang ito. Hindi ito ise-save bilang iyong plano.",
      communityTitle: "Kalagayan ng komunidad",
      riskTitle: "Resulta ng panganib",
      comparisonTitle: "Paghahambing ng pananim",
      collectiveTitle: "Sama-samang pagtingin",
      finishTitle: "Handa ka nang magsimula",
      finishBody: "Magsisimula na walang laman ang iyong totoong TANIM data. Walang planting plan na ginawa ang demo.",
      nextButton: "Susunod",
      backButton: "Bumalik",
      startButton: "Simulan ang TANIM",
      homeTitle: "Home ng TANIM",
      homeBody: "Handa ang authenticated home para sa susunod na phase ng platform. Tapos na ang iyong unang demo.",
      replayButton: "Ulitin ang demo",
      logoutButton: "Mag-logout",
      areaUnit: "ha",
      existingLabel: "Nakaplanong area",
      proposedLabel: "Iyong sample plan",
      projectedLabel: "Projected area",
      referenceLabel: "Reference",
      ratioLabel: "Ratio",
      currentPressureLabel: "Kasalukuyang pressure",
      hypotheticalPressureLabel: "Kung idagdag ang parehong area",
      periodLabel: "Panahon ng ani",
      locationLabel: "Lokasyon",
      periodSeparator: "hanggang",
      collectiveBody: "Makikita ng mga kooperatiba sa hinaharap ang pinagsamang crop plans ayon sa pananim at panahon ng ani. Demo-only data ang gamit dito.",
      demoError: "Hindi maikarga ang demo ngayon. Suriin ang local API at data seed, pagkatapos ay subukan muli.",
      retryButton: "Subukan muli",
      explanation: (crop, existing, proposed, projected, reference, ratio, risk) =>
        `Ang nakaplanong ${crop} ay ${existing} ha. Kapag idinagdag ang ${proposed} ha, magiging ${projected} ha ito laban sa ${reference} ha na reference. Ang supply pressure ratio ay ${ratio}, na ${risk}.`,
    },
    riskLabels: { low: "Mababa", moderate: "Katamtaman", high: "Mataas" },
    errors: {
      INVALID_EMAIL: "Maglagay ng wastong email address.",
      INVALID_PASSWORD: "Gumamit ng hindi bababa sa 8 character para sa password.",
      INVALID_ROLE: "Pumili ng Magsasaka o Kooperatiba.",
      PRIVACY_CONSENT_REQUIRED: "Tanggapin ang kinakailangang Privacy Notice bago gumawa ng account.",
      PRIVACY_NOTICE_VERSION_UNSUPPORTED: "Nagbago ang Privacy Notice. Buksan itong muli at magpatuloy.",
      EMAIL_ALREADY_REGISTERED: "Nakarehistro na ang email na ito. Subukan ang pag-login.",
      INVALID_CREDENTIALS: "Mali ang email o password.",
      UNAUTHENTICATED: "Mag-login para magpatuloy.",
      CSRF_INVALID: "I-refresh ang page at subukan muli.",
      DATABASE_UNAVAILABLE: "Hindi makakonekta ang TANIM sa local service. Suriin ang PostgreSQL at subukan muli.",
      DATASET_NOT_READY: "Hindi pa handa ang TANIM demo data. Patakbuhin ang data seed at subukan muli.",
    },
  },
};

export { phase5Messages } from "./platform";
