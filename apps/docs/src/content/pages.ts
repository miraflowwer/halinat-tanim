import type { DocumentPage, PageCopy } from "./types";

function page(
  route: string,
  section: DocumentPage["section"],
  en: PageCopy,
  tl: PageCopy,
  related: string[] = [],
): DocumentPage {
  return { route, section, en, tl, related };
}

export const pages: DocumentPage[] = [
  page(
    "/",
    "introduction",
    {
      title: "Introduction",
      description: "What TANIM does, who it serves, and where it works today.",
      blocks: [
        {
          kind: "text",
          heading: "What is TANIM?",
          paragraphs: [
            "TANIM means Timely Agricultural Network for Informed Market. It helps farmers and cooperatives review registered crop plans before planting decisions are final.",
            "Farmers may not know how much of the same crop other farmers plan to grow for a similar harvest period. If many plans overlap, expected supply may be high. TANIM compares registered plans with a reference level and explains the result as Glut Risk.",
          ],
        },
        {
          kind: "callout",
          calloutKind: "important",
          title: "A planning aid",
          text: "TANIM gives a supply pressure indicator. It cannot promise a market price, sale, or profit.",
        },
        {
          kind: "list",
          heading: "Current scope",
          items: [
            "Luzon, Philippines",
            "Farmers and cooperatives",
            "Region, Province, and Municipality or City detail",
            "Mobile and desktop web on localhost",
            "English and Tagalog",
          ],
        },
        {
          kind: "text",
          heading: "What this documentation covers",
          paragraphs: [
            "The TANIM Engine page describes the Phase 3 code in this repository. Other product areas are described where the repository supports the details. Some guides are short because their scope is limited in this version.",
          ],
        },
      ],
    },
    {
      title: "Panimula",
      description: "Alamin kung ano ang ginagawa ng TANIM, para kanino ito, at saan ito magagamit ngayon.",
      blocks: [
        {
          kind: "text",
          heading: "Ano ang TANIM?",
          paragraphs: [
            "Ang TANIM ay nangangahulugang Timely Agricultural Network for Informed Market. Tinutulungan nito ang mga magsasaka at kooperatiba na suriin ang mga rehistradong planong pananim bago magpasya sa pagtatanim.",
            "Maaaring hindi alam ng isang magsasaka kung gaano karaming kapwa magsasaka ang nagpaplanong magtanim ng kaparehong pananim para sa halos parehong panahon ng anihan. Kapag nagsabay-sabay ang maraming plano, maaaring mataas ang inaasahang supply. Inihahambing ng TANIM ang mga rehistradong plano sa isang batayang antas at ipinapaliwanag ang resulta bilang Glut Risk.",
          ],
        },
        {
          kind: "callout",
          calloutKind: "important",
          title: "Pantulong sa pagpaplano",
          text: "Nagbibigay ang TANIM ng palatandaan tungkol sa pressure sa supply. Hindi nito ginagarantiya ang presyo, benta, o kita.",
        },
        {
          kind: "list",
          heading: "Kasalukuyang saklaw",
          items: [
            "Luzon, Pilipinas",
            "Mga magsasaka at kooperatiba",
            "Antas ng Region, Province, at Municipality or City",
            "Mobile at desktop web sa localhost",
            "English at Tagalog",
          ],
        },
        {
          kind: "text",
          heading: "Nilalaman ng gabay na ito",
          paragraphs: [
            "Inilalarawan ng pahina ng TANIM Engine ang Phase 3 code sa repository na ito. Inilalarawan lamang ang ibang bahagi ng produkto kapag may batayan sa repository. Maikli muna ang ilang gabay habang hindi pa available ang kaugnay na daloy sa bersyong ito.",
          ],
        },
      ],
    },
    ["/getting-started", "/engine", "/data", "/limitations"],
  ),
  page(
    "/getting-started",
    "getting-started",
    {
      title: "Getting Started",
      description: "Start TANIM on a local Windows computer and open its local pages.",
      blocks: [
        {
          kind: "list",
          heading: "Start TANIM locally",
          items: [
            "Install the local tools listed in the repository README.",
            "Set DATABASE_URL in a local .env file and prepare the local database as described in README.md.",
            "Run TANIM.bat. The launcher checks local tools and services. It asks before installing missing software.",
            "Wait until TANIM reports that it is ready. The launcher opens the landing page at http://127.0.0.1:3000.",
            "Open the documentation at http://127.0.0.1:3003.",
          ],
        },
        {
          kind: "callout",
          calloutKind: "note",
          title: "Accounts and the first demo",
          text: "New users read the Privacy Notice and register as a Farmer or Cooperative user. TANIM then shows a seven-step first-time demo with sample data. The demo does not save a planting plan. After the demo, Farmers can create and manage their own plans, and Cooperative users can open their organization overview.",
        },
        {
          kind: "text",
          heading: "Explore the engine example",
          paragraphs: [
            "The Phase 3 engine powers the platform's risk preview. Read How Glut Risk Works and the Engine Example to understand its inputs and result.",
          ],
        },
      ],
    },
    {
      title: "Pagsisimula",
      description: "Simulan ang TANIM sa lokal na Windows computer at buksan ang mga lokal na pahina nito.",
      blocks: [
        {
          kind: "list",
          heading: "Simulan ang TANIM sa lokal na computer",
          items: [
            "I-install ang mga lokal na tool na nakalista sa README ng repository.",
            "Itakda ang DATABASE_URL sa lokal na .env file at ihanda ang database ayon sa README.md.",
            "Patakbuhin ang TANIM.bat. Sinusuri nito ang mga lokal na tool at serbisyo. Nagtatanong muna ito bago mag-install ng nawawalang software.",
            "Hintaying sabihin ng TANIM na handa na ito. Binubuksan ng launcher ang landing page sa http://127.0.0.1:3000.",
            "Buksan ang dokumentasyon sa http://127.0.0.1:3003.",
          ],
        },
        {
          kind: "callout",
          calloutKind: "note",
          title: "Account at unang demo",
          text: "Binabasa muna ng mga bagong user ang Privacy Notice at nagrerehistro bilang magsasaka o kooperatiba. Pagkatapos, ipinapakita ng TANIM ang pitong-hakbang na unang demo gamit ang halimbawang datos. Hindi nagse-save ng planong pananim ang demo. Pagkatapos ng demo, maaaring gumawa at mamahala ng sariling plano ang magsasaka. Maaaring buksan ng Cooperative user ang overview ng kanilang organisasyon.",
        },
        {
          kind: "text",
          heading: "Tingnan ang halimbawa ng engine",
          paragraphs: [
            "Pinapagana ng Phase 3 engine ang risk preview ng platform. Basahin ang Paano Gumagana ang Glut Risk at Halimbawa ng Engine upang malaman ang mga input at resulta nito.",
          ],
        },
      ],
    },
    ["/", "/engine", "/engine/example", "/help/faq"],
  ),
  page(
    "/farmers",
    "farmer-guide",
    {
      title: "Farmer Guide",
      description: "Understand the planting plan and Glut Risk flow TANIM is designed to support.",
      blocks: [
        {
          kind: "text",
          heading: "Before you plan",
          paragraphs: [
            "TANIM is designed to help a farmer compare a proposed crop and area with relevant plans and a reference for the same supported place and harvest period.",
            "The Phase 3 engine accepts a crop, a Municipality or City, a proposed area in hectares, harvest dates, and optional comparison crops. It returns a preview with an explanation. The engine does not save a planting plan.",
          ],
        },
        {
          kind: "list",
          heading: "Available account and demo steps",
          items: [
            "Read the Privacy Notice, then register as a Farmer, or sign in to an existing account.",
            "Complete the first-time demo. It shows sample Tomato and Eggplant scenarios.",
            "Use the demo to see the Glut Risk explanation and crop comparison.",
          ],
        },
        {
          kind: "callout",
          calloutKind: "limitation",
          title: "Implemented flow",
          text: "The demo uses sample data and does not save a planting plan. After the demo, a Farmer can create, preview, save, edit, and cancel an owned plan. Crop, price, suitability, supply map, and weather screens are available as separate context tools.",
        },
      ],
    },
    {
      title: "Gabay para sa Magsasaka",
      description: "Unawain ang daloy ng planong pananim at Glut Risk na layuning suportahan ng TANIM.",
      blocks: [
        {
          kind: "text",
          heading: "Bago magplano",
          paragraphs: [
            "Dinisenyo ang TANIM upang tulungan ang magsasaka na ihambing ang iminungkahing pananim at lawak nito sa mga kaugnay na plano at batayan para sa parehong sinusuportahang lugar at panahon ng anihan.",
            "Tumatanggap ang Phase 3 engine ng pananim, Municipality or City, iminungkahing lawak sa ektarya, mga petsa ng anihan, at opsyonal na mga pananim na ihahambing. Nagbabalik ito ng preview at paliwanag. Hindi nagse-save ng planong pananim ang engine.",
          ],
        },
        {
          kind: "list",
          heading: "Mga available na hakbang para sa account at demo",
          items: [
            "Basahin ang Privacy Notice at magparehistro bilang magsasaka, o mag-sign in sa dati nang account.",
            "Kumpletuhin ang unang demo. Ipinapakita nito ang mga halimbawang sitwasyon ng Tomato at Eggplant.",
            "Gamitin ang demo upang makita ang paliwanag ng Glut Risk at paghahambing ng pananim.",
          ],
        },
        {
          kind: "callout",
          calloutKind: "limitation",
          title: "Katayuan ng gabay",
          text: "Gumagamit ng halimbawang datos ang demo at hindi ito nagse-save ng planong pananim. Pagkatapos ng demo, maaaring gumawa, mag-preview, mag-save, mag-edit, at mag-cancel ng sariling plano ang Farmer. Available bilang hiwalay na context tool ang Crop Library, presyo, kaangkupan, supply map, at weather.",
        },
      ],
    },
    ["/engine", "/engine/risk-levels", "/crops", "/limitations"],
  ),
  page(
    "/cooperatives",
    "cooperative-guide",
    {
      title: "Cooperative Guide",
      description: "Learn the intended role of cooperative crop planning in TANIM.",
      blocks: [
        {
          kind: "text",
          heading: "A shared crop picture",
          paragraphs: [
            "TANIM is designed to help a cooperative review aggregated crop plans by crop, place, and harvest period. This can help members discuss expected supply before planting decisions are final.",
            "The product requirements describe shared crop information and context such as supply, price, suitability, maps, and weather. They do not require advanced organization administration.",
          ],
        },
        {
          kind: "callout",
          calloutKind: "limitation",
          title: "Implemented flow",
          text: "A Cooperative user can register and sign in. The cooperative overview shows active plans linked to the user's organization, grouped by crop, place, and planning period. It does not show Farmer names, email addresses, or user IDs, and it is not an advanced administration screen.",
        },
        {
          kind: "list",
          heading: "Topics to review in the cooperative view",
          items: [
            "Aggregated plans by crop and period",
            "The selected geographic context",
            "Supply pressure and its reference level",
            "Shared crop information and available map or weather context",
          ],
        },
      ],
    },
    {
      title: "Gabay para sa Kooperatiba",
      description: "Alamin ang layuning papel ng pagpaplano ng pananim ng kooperatiba sa TANIM.",
      blocks: [
        {
          kind: "text",
          heading: "Pinagsasaluhang larawan ng pananim",
          paragraphs: [
            "Dinisenyo ang TANIM upang tulungan ang kooperatiba na suriin ang pinagsama-samang mga plano ayon sa pananim, lugar, at panahon ng anihan. Makakatulong ito sa usapan ng mga kasapi tungkol sa inaasahang supply bago matapos ang pasya sa pagtatanim.",
            "Inilalarawan ng mga requirement ng produkto ang pinagsasaluhang impormasyon tungkol sa pananim at konteksto gaya ng supply, presyo, kaangkupan, mapa, at panahon. Hindi kailangan ang masalimuot na pangangasiwa ng organisasyon.",
          ],
        },
        {
          kind: "callout",
          calloutKind: "limitation",
          title: "Katayuan ng gabay",
          text: "Maaaring magparehistro at mag-sign in ang mga gumagamit mula sa kooperatiba. Ipinapakita ng cooperative overview ang mga aktibong planong konektado sa organisasyon ng user, ayon sa pananim, lugar, at planning period. Hindi nito ipinapakita ang pangalan, email address, o user ID ng Farmer. Hindi rin ito advanced administration screen.",
        },
        {
          kind: "list",
          heading: "Mga paksang dapat tingnan kapag available na ang view ng kooperatiba",
          items: [
            "Pinagsama-samang plano ayon sa pananim at panahon",
            "Napiling konteksto ng heograpiya",
            "Pressure sa supply at batayang antas nito",
            "Pinagsasaluhang impormasyon tungkol sa pananim at available na konteksto ng mapa o panahon",
          ],
        },
      ],
    },
    ["/data", "/engine", "/maps/supply", "/legal/ethics"],
  ),
  page(
    "/crops",
    "crop-information",
    {
      title: "Crop Library",
      description: "See which kinds of crop information the TANIM data model supports.",
      blocks: [
        {
          kind: "text",
          heading: "Crop information in one place",
          paragraphs: [
            "The TANIM data model supports a Crop Library profile for each active crop. It keeps crop identity and context together so the same crop can be used by plans, the engine, and other product views.",
          ],
        },
        {
          kind: "list",
          heading: "Supported profile fields",
          items: [
            "English name, Tagalog or common name, scientific name where available, and category",
            "Crop overview and growing-condition context",
            "Price history and supply context",
            "Soil suitability and weather context",
            "Dataset and source notes",
          ],
        },
        {
          kind: "definition",
          term: "Crop suitability and supply pressure",
          text: "Suitability describes context about a crop and a place. Supply pressure compares planned area with a reference level. A suitable crop can still have High supply pressure.",
        },
        {
          kind: "callout",
          calloutKind: "note",
          title: "Screen availability",
          text: "The platform includes a read-only Crop Library. It can filter active crops by search and category, then open a crop profile with growing context, price, supply, suitability, weather, and source links.",
        },
      ],
    },
    {
      title: "Crop Library",
      description: "Tingnan kung anong impormasyon tungkol sa pananim ang sinusuportahan ng TANIM data model.",
      blocks: [
        {
          kind: "text",
          heading: "Impormasyon ng pananim sa isang lugar",
          paragraphs: [
            "Sinusuportahan ng TANIM data model ang Crop Library profile para sa bawat aktibong pananim. Pinagsasama nito ang pagkakakilanlan at konteksto ng pananim upang magamit ito sa mga plano, engine, at iba pang view ng produkto.",
          ],
        },
        {
          kind: "list",
          heading: "Mga field ng profile",
          items: [
            "Pangalan sa English, Tagalog o karaniwang pangalan, siyentipikong pangalan kung mayroon, at kategorya",
            "Pangkalahatang-ideya ng pananim at konteksto ng kondisyon sa pagtatanim",
            "Kasaysayan ng presyo at konteksto ng supply",
            "Kaangkupan ng lupa at konteksto ng panahon",
            "Mga tala tungkol sa dataset at pinagmulan",
          ],
        },
        {
          kind: "definition",
          term: "Kaangkupan ng pananim at pressure sa supply",
          text: "Inilalarawan ng kaangkupan ang konteksto ng pananim at lugar. Inihahambing naman ng pressure sa supply ang planong lawak sa batayang antas. Maaari pa ring magkaroon ng High supply pressure ang angkop na pananim.",
        },
        {
          kind: "callout",
          calloutKind: "note",
          title: "Availability ng screen",
          text: "May read-only Crop Library ang platform. Maaari nitong i-filter ang mga aktibong pananim ayon sa search at category, at buksan ang crop profile na may growing context, presyo, supply, kaangkupan, weather, at source links.",
        },
      ],
    },
    ["/crops/prices", "/crops/suitability", "/data", "/data/sources"],
  ),
  page(
    "/crops/prices",
    "crop-information",
    {
      title: "Price History",
      description: "Understand the units, place, and demo status of TANIM price records.",
      blocks: [
        {
          kind: "text",
          heading: "Reading price records",
          paragraphs: [
            "TANIM price records use Philippine pesos per kilogram (PHP/kg). The Price History screen filters records by crop, supported location, and time range, with optional start and end dates.",
            "The current demo series is synthetic. It helps test how a history view may work. It is not a list of exact government prices or proof of the price a farmer will receive.",
          ],
        },
        {
          kind: "callout",
          calloutKind: "data",
          title: "Synthetic price history",
          text: "The generated price series is marked synthetic in its data metadata. PSA and DA sources inform data shape and crop context, not the exact TANIM numbers.",
        },
        {
          kind: "callout",
          calloutKind: "limitation",
          title: "Screen availability",
          text: "The Price History screen includes a keyboard-readable chart and a table view. It shows the dataset version and marks generated values as synthetic demo data.",
        },
      ],
    },
    {
      title: "Kasaysayan ng Presyo",
      description: "Unawain ang yunit, lugar, at demo status ng mga price record sa TANIM.",
      blocks: [
        {
          kind: "text",
          heading: "Pagbasa sa mga record ng presyo",
          paragraphs: [
            "Gumagamit ang mga price record ng TANIM ng Philippine pesos bawat kilo (PHP/kg). Sa Price History screen, maaaring pumili ng pananim, sinusuportahang lugar, at time range. Maaari ring magtakda ng petsa ng simula at pagtatapos.",
            "Synthetic ang kasalukuyang demo series. Tumutulong ito sa pagsubok kung paano maaaring gumana ang history view. Hindi ito listahan ng eksaktong presyo ng gobyerno o patunay ng presyong matatanggap ng magsasaka.",
          ],
        },
        {
          kind: "callout",
          calloutKind: "data",
          title: "Synthetic na kasaysayan ng presyo",
          text: "Minarkahang synthetic sa metadata ng datos ang nabuong series ng presyo. Gabay ang mga source ng PSA at DA sa hugis ng datos at konteksto ng pananim, hindi sa eksaktong mga numero ng TANIM.",
        },
        {
          kind: "callout",
          calloutKind: "limitation",
          title: "Availability ng screen",
          text: "May keyboard-readable chart at table view ang Price History screen. Ipinapakita nito ang dataset version at minamarkahan bilang synthetic demo data ang mga nabuong value.",
        },
      ],
    },
    ["/crops", "/data/sources", "/data/synthetic-data", "/limitations"],
  ),
  page(
    "/crops/suitability",
    "crop-information",
    {
      title: "Soil Suitability",
      description: "Learn what suitability labels mean and how they differ from Glut Risk.",
      blocks: [
        {
          kind: "list",
          heading: "Suitability labels",
          items: [
            "Suitable: the dataset marks this crop and place as suitable context.",
            "Moderately Suitable: the dataset marks a middle suitability category.",
            "Low Suitability: the dataset marks lower suitability context.",
            "No Data: no usable label is available for this combination.",
          ],
        },
        {
          kind: "definition",
          term: "Suitability is not Glut Risk",
          text: "Soil suitability is context about a place and crop. Glut Risk is a supply pressure result from planned area and a reference area. One does not calculate the other.",
        },
        {
          kind: "callout",
          calloutKind: "data",
          title: "Demo data status",
          text: "The current generated suitability labels are TANIM synthetic demo data. They are not a real soil survey or an official NCCAG or BSWM classification.",
        },
        {
          kind: "callout",
          calloutKind: "limitation",
          title: "Screen availability",
          text: "The Soil Suitability screen lets a user choose a crop and supported location. It shows a suitability label, method note, dataset version, and source context when available.",
        },
      ],
    },
    {
      title: "Kaangkupan ng Lupa",
      description: "Alamin ang kahulugan ng mga label ng kaangkupan at ang kaibahan ng mga ito sa Glut Risk.",
      blocks: [
        {
          kind: "list",
          heading: "Mga label ng kaangkupan",
          items: [
            "Suitable: minamarkahan ng dataset na angkop ang konteksto ng pananim at lugar.",
            "Moderately Suitable: minamarkahan ng dataset ang katamtamang kategorya ng kaangkupan.",
            "Low Suitability: minamarkahan ng dataset ang mas mababang konteksto ng kaangkupan.",
            "No Data: walang magagamit na label para sa kombinasyong ito.",
          ],
        },
        {
          kind: "definition",
          term: "Hindi Glut Risk ang kaangkupan",
          text: "Konteksto ng lugar at pananim ang soil suitability. Resulta naman ng pressure sa supply ang Glut Risk batay sa planong lawak at reference area. Hindi kinukuwenta ng isa ang isa pa.",
        },
        {
          kind: "callout",
          calloutKind: "data",
          title: "Katayuan ng demo data",
          text: "TANIM synthetic demo data ang kasalukuyang nabuong mga label ng kaangkupan. Hindi ito tunay na soil survey o opisyal na klasipikasyon ng NCCAG o BSWM.",
        },
        {
          kind: "callout",
          calloutKind: "limitation",
          title: "Availability ng screen",
          text: "Sa Soil Suitability screen, pumipili ang user ng pananim at sinusuportahang lugar. Ipinapakita nito ang label ng kaangkupan, method note, dataset version, at source context kung mayroon.",
        },
      ],
    },
    ["/crops", "/engine/risk-levels", "/data/synthetic-data", "/limitations"],
  ),
  page(
    "/maps",
    "maps-weather",
    {
      title: "Maps and Weather",
      description: "See how TANIM separates supply context from live weather context.",
      blocks: [
        {
          kind: "text",
          heading: "Two kinds of context",
          paragraphs: [
            "The planned Supply Map shows crop supply context for supported Luzon geography. Weather is a separate live service and may need an internet connection.",
            "Weather does not affect the Phase 3 Glut Risk calculation. A weather outage must not stop local TANIM features.",
          ],
        },
        {
          kind: "callout",
          calloutKind: "limitation",
          title: "Current repository version",
          text: "The platform includes a local Supply Map and a separate Weather screen. The map uses local eight-region geometry and a text list. Weather is live external context and can fail without a reachable provider.",
        },
      ],
    },
    {
      title: "Mapa at Panahon",
      description: "Tingnan kung paano pinaghihiwalay ng TANIM ang konteksto ng supply at live na panahon.",
      blocks: [
        {
          kind: "text",
          heading: "Dalawang uri ng konteksto",
          paragraphs: [
            "Ipinapakita ng nakaplanong Supply Map ang konteksto ng supply ng pananim sa sinusuportahang heograpiya ng Luzon. Hiwalay na live service ang weather at maaaring mangailangan ng internet.",
            "Hindi nakaaapekto ang weather sa Phase 3 na pagkukuwenta ng Glut Risk. Hindi dapat mapahinto ng pagkawala ng weather ang mga lokal na feature ng TANIM.",
          ],
        },
        {
          kind: "callout",
          calloutKind: "limitation",
          title: "Kasalukuyang bersyon ng repository",
          text: "May lokal na Supply Map at hiwalay na Weather screen ang platform. Gumagamit ang mapa ng lokal na geometry para sa walong rehiyon at text list. Live external context ang weather at maaaring mabigo kapag hindi reachable ang provider.",
        },
      ],
    },
    ["/maps/supply", "/maps/weather", "/engine", "/limitations"],
  ),
  page(
    "/maps/supply",
    "maps-weather",
    {
      title: "Supply Map",
      description: "Understand the planned map labels for crop supply context.",
      blocks: [
        {
          kind: "list",
          heading: "Map context labels",
          items: [
            "Low",
            "Moderate or Balanced",
            "High",
            "No Data",
          ],
        },
        {
          kind: "text",
          heading: "How to read the map",
          paragraphs: [
            "A supply label describes the current data context for the selected crop, period, and supported geographic area. Color should not be the only signal. Read the label and any numeric context shown for the selected place.",
            "A map snapshot and the Phase 3 engine are distinct. The engine uses active registered plans and a configured future reference. A synthetic map snapshot is not a registered planting plan.",
          ],
        },
        {
          kind: "callout",
          calloutKind: "limitation",
          title: "Available map controls",
          text: "The Supply Map screen lets a user choose a crop and a current or supported future period. It shows regional labels, numeric context, dataset provenance, a local map, and a keyboard-accessible region list.",
        },
      ],
    },
    {
      title: "Supply Map",
      description: "Unawain ang mga nakaplanong label ng mapa para sa konteksto ng supply ng pananim.",
      blocks: [
        {
          kind: "list",
          heading: "Mga label ng konteksto sa mapa",
          items: ["Low", "Moderate o Balanced", "High", "No Data"],
        },
        {
          kind: "text",
          heading: "Pagbasa sa mapa",
          paragraphs: [
            "Inilalarawan ng label ng supply ang kasalukuyang konteksto ng datos para sa napiling pananim, panahon, at sinusuportahang heograpikong lugar. Hindi dapat kulay lang ang batayan. Basahin ang label at anumang numerong konteksto para sa napiling lugar.",
            "Magkaiba ang map snapshot at Phase 3 engine. Gumagamit ang engine ng mga aktibong rehistradong plano at itinakdang future reference. Hindi rehistradong planong pananim ang synthetic map snapshot.",
          ],
        },
        {
          kind: "callout",
          calloutKind: "limitation",
          title: "Hindi kumpirmado ang mga control",
          text: "Sa Supply Map screen, pumipili ang user ng pananim at kasalukuyan o sinusuportahang future period. Ipinapakita nito ang regional label, numeric context, dataset provenance, lokal na mapa, at keyboard-accessible na listahan ng rehiyon.",
        },
      ],
    },
    ["/maps", "/engine", "/data/synthetic-data", "/data/geography"],
  ),
  page(
    "/maps/weather",
    "maps-weather",
    {
      title: "Weather",
      description: "Know what a live weather request should tell you and why it may fail.",
      blocks: [
        {
          kind: "list",
          heading: "Weather service requirements",
          items: [
            "Live weather may need an internet connection.",
            "TANIM should explain the connection before it requests live weather.",
            "The service may be unavailable. TANIM should report this and offer Retry.",
            "Weather failure should not stop local TANIM features.",
          ],
        },
        {
          kind: "definition",
          term: "Weather and Glut Risk",
          text: "The Phase 3 engine does not use weather in its risk calculation.",
        },
        {
          kind: "callout",
          calloutKind: "limitation",
          title: "Provider and screen status",
          text: "The platform uses an Open-Meteo provider adapter. The user must choose Continue before a weather request. If the service fails, the screen explains the connection requirement and provides Retry. Weather remains separate from synthetic agricultural data.",
        },
      ],
    },
    {
      title: "Panahon",
      description: "Alamin kung anong impormasyon ang dapat ibigay bago humingi ng live weather at kung bakit ito maaaring mabigo.",
      blocks: [
        {
          kind: "list",
          heading: "Mga requirement ng weather service",
          items: [
            "Maaaring kailangan ng internet para sa live weather.",
            "Dapat ipaliwanag ng TANIM ang koneksyon bago humingi ng live weather.",
            "Maaaring hindi available ang service. Dapat itong ipaalam ng TANIM at magbigay ng Retry.",
            "Hindi dapat mapahinto ng problema sa weather ang mga lokal na feature ng TANIM.",
          ],
        },
        {
          kind: "definition",
          term: "Weather at Glut Risk",
          text: "Hindi ginagamit ng Phase 3 engine ang weather sa pagkukuwenta ng risk.",
        },
        {
          kind: "callout",
          calloutKind: "limitation",
          title: "Katayuan ng provider at screen",
          text: "Gumagamit ang platform ng Open-Meteo provider adapter. Kailangang piliin muna ng user ang Continue bago humingi ng weather. Kapag nabigo ang service, ipinapaliwanag ng screen ang connection requirement at nagbibigay ng Retry. Hiwalay ang weather sa synthetic agricultural data.",
        },
      ],
    },
    ["/maps", "/engine", "/help/faq", "/limitations"],
  ),
  page(
    "/engine",
    "engine",
    {
      title: "How Glut Risk Works",
      description: "A clear view of the deterministic Phase 3 TANIM Engine calculation.",
      blocks: [
        {
          kind: "text",
          heading: "A preview from defined inputs",
          paragraphs: [
            "The Phase 3 TANIM Engine uses a deterministic calculation. The same input data and configured dataset give the same result. It uses decimal arithmetic and does not round the ratio before classifying it.",
            "The engine is an API calculation. A preview returns its inputs, data versions, contributing plan count, risk level, and a plain explanation. It does not save a planting plan.",
            "Harvest dates must fit inside one configured quarter. The engine rejects a request that crosses quarters or falls outside the configured future horizon.",
          ],
        },
        {
          kind: "formula",
          heading: "The calculation",
          lines: [
            "Projected Planned Area = Existing Relevant Planned Area + Proposed Area",
            "Supply Pressure Ratio = Projected Planned Area / Reference Area",
          ],
          explanation: "Area is measured in hectares. The ratio compares projected planned area with the configured reference area.",
        },
        {
          kind: "list",
          heading: "Data used by the engine",
          items: [
            "Active registered plans for the same active crop and Municipality or City",
            "Plans whose expected harvest dates overlap the normalized planning period",
            "Cancelled, completed, other-crop, other-place, and non-overlapping plans are not counted. Synthetic supply snapshots are not registered plans.",
            "One positive future reference for the crop, place, period, and configured dataset version",
            "The proposed area supplied for the preview",
          ],
        },
        {
          kind: "callout",
          calloutKind: "important",
          title: "A missing reference means no score",
          text: "When the reference is missing or not positive, the engine returns an unavailable result with no ratio and no risk level. It does not invent a score.",
        },
      ],
    },
    {
      title: "Paano Gumagana ang Glut Risk",
      description: "Malinaw na paliwanag sa deterministic na pagkukuwenta ng Phase 3 TANIM Engine.",
      blocks: [
        {
          kind: "text",
          heading: "Preview mula sa tiyak na mga input",
          paragraphs: [
            "Gumagamit ang Phase 3 TANIM Engine ng deterministic na pagkukuwenta. Pareho ang resulta kapag pareho ang input na datos at configured dataset. Gumagamit ito ng decimal arithmetic at hindi niroround ang ratio bago tukuyin ang kategorya nito.",
            "API calculation ang engine. Ibinabalik ng preview ang mga input, bersyon ng datos, bilang ng kasamang plano, antas ng risk, at payak na paliwanag. Hindi nito sine-save ang planong pananim.",
            "Dapat pasok sa isang configured na quarter ang mga petsa ng anihan. Tinatanggihan ng engine ang planong tumatawid sa mga quarter o nasa labas ng configured na future horizon.",
          ],
        },
        {
          kind: "formula",
          heading: "Pagkukuwenta",
          lines: [
            "Projected Planned Area = Existing Relevant Planned Area + Proposed Area",
            "Supply Pressure Ratio = Projected Planned Area / Reference Area",
          ],
          explanation: "Ektarya ang yunit ng lawak. Inihahambing ng ratio ang inaasahang planong lawak sa itinakdang reference area.",
        },
        {
          kind: "list",
          heading: "Datos na ginagamit ng engine",
          items: [
            "Mga aktibong rehistradong plano para sa parehong aktibong pananim at Municipality or City",
            "Mga planong may inaasahang petsa ng anihan na sumasaklaw sa normalized na planning period",
            "Hindi binibilang ang kinansela, nakumpleto, ibang pananim, ibang lugar, o hindi nagsasabay na plano. Hindi rehistradong plano ang synthetic supply snapshot.",
            "Isang positibong future reference para sa pananim, lugar, panahon, at configured na bersyon ng dataset",
            "Iminungkahing lawak na ibinigay para sa preview",
          ],
        },
        {
          kind: "callout",
          calloutKind: "important",
          title: "Walang score kung walang reference",
          text: "Kapag nawawala o hindi positibo ang reference, nagbabalik ang engine ng unavailable na resulta na walang ratio at risk level. Hindi ito nag-iimbento ng score.",
        },
      ],
    },
    ["/engine/risk-levels", "/engine/example", "/data", "/limitations"],
  ),
  page(
    "/engine/risk-levels",
    "engine",
    {
      title: "Risk Levels",
      description: "Read the Phase 3 prototype thresholds for Low, Moderate, and High.",
      blocks: [
        {
          kind: "definition",
          term: "Low",
          text: "The Supply Pressure Ratio is below 0.90.",
        },
        {
          kind: "definition",
          term: "Moderate",
          text: "The ratio is from 0.90 through 1.10, including both endpoints.",
        },
        {
          kind: "definition",
          term: "High",
          text: "The ratio is above 1.10.",
        },
        {
          kind: "definition",
          term: "No Data or unavailable",
          text: "A usable positive reference is missing. The engine returns no ratio and no risk level.",
        },
        {
          kind: "callout",
          calloutKind: "note",
          title: "Prototype thresholds",
          text: "These are configurable prototype assumptions in engine version grci-v1. Snapshot labels use a separate rule, even though their current threshold values match. These levels are not a guarantee of what will happen in a market.",
        },
      ],
    },
    {
      title: "Mga Antas ng Panganib",
      description: "Basahin ang prototype thresholds ng Phase 3 para sa Low, Moderate, at High.",
      blocks: [
        {
          kind: "definition",
          term: "Low",
          text: "Mas mababa sa 0.90 ang Supply Pressure Ratio.",
        },
        {
          kind: "definition",
          term: "Moderate",
          text: "Nasa 0.90 hanggang 1.10 ang ratio, kabilang ang dalawang hangganan.",
        },
        {
          kind: "definition",
          term: "High",
          text: "Mas mataas sa 1.10 ang ratio.",
        },
        {
          kind: "definition",
          term: "No Data o unavailable",
          text: "Walang magagamit na positibong reference. Walang ratio at risk level na ibinabalik ang engine.",
        },
        {
          kind: "callout",
          calloutKind: "note",
          title: "Prototype thresholds",
          text: "Configurable na mga palagay ang mga ito sa prototype engine na bersyong grci-v1. Hiwalay ang rule para sa snapshot label kahit magkapareho sa ngayon ang mga threshold value. Hindi garantiya ang mga antas na ito ng mangyayari sa merkado.",
        },
      ],
    },
    ["/engine", "/engine/example", "/limitations", "/data/synthetic-data"],
  ),
  page(
    "/engine/example",
    "engine",
    {
      title: "Engine Example",
      description: "Follow the canonical Tomato example and an informational Eggplant comparison.",
      blocks: [
        {
          kind: "example",
          heading: "Tomato in Cabanatuan, 2027 quarter 1",
          values: [
            { label: "Existing planned area", value: "32 ha" },
            { label: "Proposed area", value: "8 ha" },
            { label: "Reference area", value: "25 ha" },
          ],
          calculation: "32 ha + 8 ha = 40 ha. Then 40 ha / 25 ha = 1.60.",
          result: "High",
          note: "Under the current TANIM prototype thresholds, this plan has High supply pressure. It does not mean Tomato will definitely have a glut.",
        },
        {
          kind: "example",
          heading: "Eggplant comparison for the same place and period",
          values: [
            { label: "Existing planned area", value: "12 ha" },
            { label: "Reference area", value: "18 ha" },
          ],
          calculation: "12 ha / 18 ha = about 0.666667.",
          result: "Low current pressure",
          note: "If the same proposed 8 ha were added, projected area would be 20 ha and the ratio about 1.111111, which is High. This is an informational comparison, not a claim that Eggplant is best, more profitable, or guaranteed safer.",
        },
      ],
    },
    {
      title: "Halimbawa ng Engine",
      description: "Sundan ang canonical na halimbawa ng Tomato at ang impormatibong paghahambing sa Eggplant.",
      blocks: [
        {
          kind: "example",
          heading: "Tomato sa Cabanatuan, unang quarter ng 2027",
          values: [
            { label: "Umiiral na planong lawak", value: "32 ha" },
            { label: "Iminungkahing lawak", value: "8 ha" },
            { label: "Reference area", value: "25 ha" },
          ],
          calculation: "32 ha + 8 ha = 40 ha. Pagkatapos, 40 ha / 25 ha = 1.60.",
          result: "High",
          note: "Sa ilalim ng kasalukuyang prototype thresholds ng TANIM, High ang pressure sa supply ng planong ito. Hindi ibig sabihin nito na tiyak na magkakaroon ng glut sa Tomato.",
        },
        {
          kind: "example",
          heading: "Paghahambing sa Eggplant sa parehong lugar at panahon",
          values: [
            { label: "Umiiral na planong lawak", value: "12 ha" },
            { label: "Reference area", value: "18 ha" },
          ],
          calculation: "12 ha / 18 ha = humigit-kumulang 0.666667.",
          result: "Low ang kasalukuyang pressure",
          note: "Kung idagdag ang parehong iminungkahing 8 ha, magiging 20 ha ang inaasahang lawak at humigit-kumulang 1.111111 ang ratio, kaya High ito. Impormatibong paghahambing lamang ito. Hindi nito sinasabing pinakamahusay, mas kikita, o tiyak na mas ligtas ang Eggplant.",
        },
      ],
    },
    ["/engine", "/engine/risk-levels", "/data/synthetic-data", "/limitations"],
  ),
  page(
    "/data",
    "data",
    {
      title: "TANIM Data Overview",
      description: "Learn what TANIM data groups contain and how their source is described.",
      blocks: [
        {
          kind: "list",
          heading: "Main data groups",
          items: [
            "Crop Registry: stable crop IDs, names, categories, and active status.",
            "Geography Registry: supported Luzon regions, provinces, and municipalities or cities.",
            "Planting plans: user-entered crop, place, area, dates, owner, and lifecycle status.",
            "Crop references: a comparison area used by the Phase 3 engine for a future crop and place period.",
            "Price history and supply snapshots: time-based demo context for their product views.",
            "Soil suitability and crop profiles: crop and place context with source and method notes.",
            "Dataset versions and provenance: data kind, version, units, scope, methods, and references.",
          ],
        },
        {
          kind: "callout",
          calloutKind: "data",
          title: "Know what kind of data you are reading",
          text: "TANIM marks generated agricultural values as synthetic demo data. Live weather is separate and must not be filled with generated current conditions.",
        },
        {
          kind: "text",
          heading: "Sources and methods",
          paragraphs: [
            "Public sources can inform names, geography, data structure, or broad context. That does not mean they published each generated TANIM number. See Data Sources and Synthetic Data for the recorded methods and limits.",
          ],
        },
      ],
    },
    {
      title: "Pangkalahatang-ideya ng Datos ng TANIM",
      description: "Alamin kung ano ang laman ng mga pangkat ng datos ng TANIM at paano inilalarawan ang pinagmulan ng mga ito.",
      blocks: [
        {
          kind: "list",
          heading: "Pangunahing pangkat ng datos",
          items: [
            "Crop Registry: matatag na crop ID, pangalan, kategorya, at aktibong status.",
            "Geography Registry: mga sinusuportahang rehiyon, lalawigan, munisipalidad, o lungsod sa Luzon.",
            "Mga planong pananim: pananim, lugar, lawak, petsa, owner, at lifecycle status na inilalagay ng user.",
            "Crop references: batayang lawak na ginagamit ng Phase 3 engine para ihambing ang pananim at lugar sa isang future period.",
            "Kasaysayan ng presyo at supply snapshot: konteksto ng demo batay sa panahon para sa kanilang product view.",
            "Soil suitability at crop profile: konteksto ng pananim at lugar na may tala ng source at paraan.",
            "Bersyon ng dataset at provenance: uri ng datos, bersyon, yunit, saklaw, paraan, at sanggunian.",
          ],
        },
        {
          kind: "callout",
          calloutKind: "data",
          title: "Alamin kung anong uri ng datos ang binabasa",
          text: "Minamarkahan ng TANIM bilang synthetic demo data ang mga nabuong agricultural value. Hiwalay ang live weather at hindi ito dapat palitan ng nabuong kasalukuyang lagay ng panahon.",
        },
        {
          kind: "text",
          heading: "Mga source at paraan",
          paragraphs: [
            "Maaaring maging gabay ang mga pampublikong source sa pangalan, heograpiya, istruktura ng datos, o pangkalahatang konteksto. Hindi ibig sabihin nito na sila ang naglathala ng bawat nabuong numero ng TANIM. Tingnan ang Data Sources at Synthetic Data para sa mga naitalang paraan at limitasyon.",
          ],
        },
      ],
    },
    ["/data/sources", "/data/synthetic-data", "/data/geography", "/engine"],
  ),
  page(
    "/data/sources",
    "data",
    {
      title: "Data Sources",
      description: "Sources and uses recorded in the TANIM repository source notes.",
      blocks: [
        {
          kind: "text",
          heading: "How TANIM uses sources",
          paragraphs: [
            "This list follows data/sources/SOURCES.md. Public reference sources, third-party convenience data, and TANIM synthetic methods have different roles. Source use does not make synthetic values official measurements.",
          ],
        },
        {
          kind: "sources",
          items: [
            {
              name: "PSGC summary and downloads, Second Quarter 2026",
              category: "Official public source: Philippine Statistics Authority (PSA)",
              use: "Geographic authority, names, codes, hierarchy, and a cross-check of Luzon coverage. TANIM also records that PSGC Cloud supplied the structured convenience copy used for extraction.",
              url: "https://psa.gov.ph/classification/psgc/summary",
              terms: "The source notes state CC BY 4.0 for PSA website content unless otherwise noted.",
            },
            {
              name: "PSGC Cloud API v2: regions endpoint",
              category: "Third-party convenience source, not a PSA service",
              use: "Structured extraction of region names and codes. PSA records were checked for authority and coverage totals.",
              url: "https://psgc.cloud/api/v2/regions",
              terms: "The source notes make no separate license claim for the API copy.",
            },
            {
              name: "PSGC Cloud API v2: provinces endpoint",
              category: "Third-party convenience source, not a PSA service",
              use: "Structured extraction of province names and codes for the geography registry.",
              url: "https://psgc.cloud/api/v2/provinces",
              terms: "The source notes make no separate license claim for the API copy.",
            },
            {
              name: "PSGC Cloud API v2: cities and municipalities endpoint",
              category: "Third-party convenience source, not a PSA service",
              use: "Structured extraction of city and municipality names and codes for the geography registry.",
              url: "https://psgc.cloud/api/v2/cities-municipalities",
              terms: "The source notes make no separate license claim for the API copy.",
            },
            {
              name: "PSA OpenSTAT table 2M4AFN08",
              category: "Official public source: Philippine Statistics Authority",
              use: "Farmgate price data concepts, reporting frequency, and available geographic levels. TANIM does not copy those values into its synthetic series.",
              url: "https://openstat.psa.gov.ph/Metadata/2M4AFN08",
              terms: "The source notes state CC BY 4.0 for PSA website content unless otherwise noted.",
            },
            {
              name: "DA Price Monitoring",
              category: "Official public source: Department of Agriculture (DA)",
              use: "Marketed crop coverage and broad retail price context. Demo price baselines are manual and are not statistically calibrated to the published prices.",
              url: "https://www.da.gov.ph/price-monitoring/",
              terms: "The source notes say no specific data license was stated on the page.",
            },
            {
              name: "DA Price Monitoring report, 25 February 2026",
              category: "Official public source: Department of Agriculture",
              use: "Cross-check of commodity coverage, including White Potato, Chayote, Celery, and Baguio Beans. Report prices are not copied into generated TANIM values.",
              url: "https://www.da.gov.ph/wp-content/uploads/2026/02/Price-Monitoring-February-25-2026.pdf",
              terms: "The source notes say no specific data license was stated in the report.",
            },
            {
              name: "2022 Crops Production in Quezon, PSA Statistical Release No. 2025-172",
              category: "Official public source: PSA CALABARZON",
              use: "Broad local crop list and naming context. Its production values are not copied into TANIM data, and Quezon coverage does not imply that every crop is grown in every TANIM location.",
              url: "https://rsso04a.psa.gov.ph/sites/default/files/attachment-dir/Region04A-56_SR%20No.%202025-172_2022%20Crops%20Production%20in%20Quezon.pdf",
              terms: "The source notes state CC BY 4.0 for PSA website content unless otherwise noted.",
            },
            {
              name: "2025 Vegetable and Root Crops Situation in Quezon, PSA Statistical Release No. 2026-100",
              category: "Official public source: PSA CALABARZON",
              use: "Cross-check of crop names and coverage. Its production values are not copied into TANIM data.",
              url: "https://rsso04a.psa.gov.ph/sites/default/files/attachment-dir/Region04A-56_SR%20No.%202026-100_2025%20Crops%20Production%20in%20Quezon.pdf",
              terms: "The source notes state CC BY 4.0 for PSA website content unless otherwise noted.",
            },
            {
              name: "2010-2025 Strawberry Situationer: Province of Benguet",
              category: "Official public source: PSA Cordillera Administrative Region",
              use: "Confirms Strawberry as a significant Benguet fruit crop. Production values are not copied into generated TANIM values.",
              url: "https://rssocar.psa.gov.ph/content/2010-2025-strawberry-situationer-province-benguet",
              terms: "The source notes state CC BY 4.0 for PSA website content unless otherwise noted.",
            },
            {
              name: "2025 First Quarter Other Crops Production Situation in Benguet",
              category: "Official public source: PSA Cordillera Administrative Region",
              use: "Confirms Strawberry, Lemon, and Chinese cabbage crop coverage in Benguet. Production values are not copied into generated TANIM values.",
              url: "https://rssocar.psa.gov.ph/content/2025-first-quarter-other-crops-production-situation-benguet",
              terms: "The source notes state CC BY 4.0 for PSA website content unless otherwise noted.",
            },
            {
              name: "Situation of Selected High Value Crops of Benguet, January-June 2025",
              category: "Official public source: PSA Cordillera Administrative Region",
              use: "Confirms Chinese cabbage and sweet peas as marketed Benguet crops. Production values are not copied into generated TANIM values.",
              url: "https://rssocar.psa.gov.ph/content/situation-selected-high-value-crops-benguet-january-june-2025",
              terms: "The source notes state CC BY 4.0 for PSA website content unless otherwise noted.",
            },
            {
              name: "Plants of the World Online",
              category: "Reference database: Royal Botanic Gardens, Kew",
              use: "Consulted for selected scientific names. The source notes do not say that every registry name was checked against this database.",
              url: "https://powo.science.kew.org/",
              terms: "See Kew terms for database use, as recorded in the source notes.",
            },
            {
              name: "National Color-Coded Agricultural Guide (NCCAG) Map 2.0 announcement",
              category: "Official public source: Department of Agriculture",
              use: "Conceptual reference for future crop and location suitability guidance. No NCCAG or BSWM location-level layer was used to create the current synthetic suitability rows.",
              url: "https://www.da.gov.ph/da-launches-updated-color-coded-agri-map-to-help-farmers-address-climate-vulnerability-and-boost-yield-income/",
              terms: "The source notes say no specific data license was stated on the article.",
            },
          ],
        },
        {
          kind: "callout",
          calloutKind: "data",
          title: "TANIM synthetic method",
          text: "Generated prices, areas, ratios, and suitability labels are synthetic demo values. The source notes name separate TANIM methods for profiles, reference areas, supply context, and soil suitability. They are not values published by PSA, DA, Kew, PSGC Cloud, NCCAG, or BSWM.",
        },
      ],
    },
    {
      title: "Mga Pinagmulan ng Datos",
      description: "Mga source at gamit na nakatala sa source notes ng TANIM repository.",
      blocks: [
        {
          kind: "text",
          heading: "Paggamit ng TANIM sa mga source",
          paragraphs: [
            "Sinusunod ng listahang ito ang data/sources/SOURCES.md. Magkakaiba ang gamit ng mga pampublikong sanggunian, third-party convenience data, at synthetic na paraan ng TANIM. Hindi ginagawang opisyal na sukat ng paggamit ng source ang synthetic na value.",
          ],
        },
        {
          kind: "sources",
          items: [
            {
              name: "PSGC summary at downloads, Ikalawang Quarter 2026",
              category: "Opisyal na pampublikong source: Philippine Statistics Authority (PSA)",
              use: "Sanggunian para sa heograpiya, pangalan, code, hierarchy, at pagsusuri sa saklaw ng Luzon. Itinatala rin ng TANIM na PSGC Cloud ang nagbigay ng structured na kopyang ginamit sa pagkuha ng datos.",
              url: "https://psa.gov.ph/classification/psgc/summary",
              terms: "Ayon sa source notes, CC BY 4.0 ang nilalaman ng website ng PSA maliban kung may ibang nakasaad.",
            },
            {
              name: "PSGC Cloud API v2: regions endpoint",
              category: "Third-party convenience source, hindi serbisyo ng PSA",
              use: "Structured na pagkuha ng pangalan at code ng rehiyon. Sinuri ang mga tala ng PSA para sa awtoridad at kabuuang saklaw.",
              url: "https://psgc.cloud/api/v2/regions",
              terms: "Walang hiwalay na license claim para sa API copy sa source notes.",
            },
            {
              name: "PSGC Cloud API v2: provinces endpoint",
              category: "Third-party convenience source, hindi serbisyo ng PSA",
              use: "Structured na pagkuha ng pangalan at code ng lalawigan para sa geography registry.",
              url: "https://psgc.cloud/api/v2/provinces",
              terms: "Walang hiwalay na license claim para sa API copy sa source notes.",
            },
            {
              name: "PSGC Cloud API v2: cities and municipalities endpoint",
              category: "Third-party convenience source, hindi serbisyo ng PSA",
              use: "Structured na pagkuha ng pangalan at code ng lungsod at munisipalidad para sa geography registry.",
              url: "https://psgc.cloud/api/v2/cities-municipalities",
              terms: "Walang hiwalay na license claim para sa API copy sa source notes.",
            },
            {
              name: "PSA OpenSTAT table 2M4AFN08",
              category: "Opisyal na pampublikong source: Philippine Statistics Authority",
              use: "Mga konsepto ng farmgate price data, dalas ng pag-uulat, at mga available na antas ng heograpiya. Hindi kinokopya ng TANIM ang mga value nito sa synthetic series.",
              url: "https://openstat.psa.gov.ph/Metadata/2M4AFN08",
              terms: "Ayon sa source notes, CC BY 4.0 ang nilalaman ng website ng PSA maliban kung may ibang nakasaad.",
            },
            {
              name: "DA Price Monitoring",
              category: "Opisyal na pampublikong source: Department of Agriculture (DA)",
              use: "Saklaw ng mga panindang pananim at pangkalahatang konteksto ng retail price. Mano-manong itinakda ang demo price baseline at hindi ito iniayon sa nailathalang presyo sa paraang estadistikal.",
              url: "https://www.da.gov.ph/price-monitoring/",
              terms: "Ayon sa source notes, walang partikular na data license na nakasaad sa pahina.",
            },
            {
              name: "DA Price Monitoring report, 25 February 2026",
              category: "Opisyal na pampublikong source: Department of Agriculture",
              use: "Pagsusuri sa saklaw ng commodity, kabilang ang White Potato, Chayote, Celery, at Baguio Beans. Hindi kinokopya sa nabuong value ng TANIM ang presyo sa report.",
              url: "https://www.da.gov.ph/wp-content/uploads/2026/02/Price-Monitoring-February-25-2026.pdf",
              terms: "Ayon sa source notes, walang partikular na data license na nakasaad sa report.",
            },
            {
              name: "2022 Crops Production in Quezon, PSA Statistical Release No. 2025-172",
              category: "Opisyal na pampublikong source: PSA CALABARZON",
              use: "Pangkalahatang listahan at pangalan ng lokal na pananim. Hindi kinokopya ang mga production value nito sa datos ng TANIM. Hindi rin ibig sabihin ng saklaw nito sa Quezon na itinatanim ang bawat pananim sa lahat ng lugar ng TANIM.",
              url: "https://rsso04a.psa.gov.ph/sites/default/files/attachment-dir/Region04A-56_SR%20No.%202025-172_2022%20Crops%20Production%20in%20Quezon.pdf",
              terms: "Ayon sa source notes, CC BY 4.0 ang nilalaman ng website ng PSA maliban kung may ibang nakasaad.",
            },
            {
              name: "2025 Vegetable and Root Crops Situation in Quezon, PSA Statistical Release No. 2026-100",
              category: "Opisyal na pampublikong source: PSA CALABARZON",
              use: "Pagsusuri sa mga pangalan at saklaw ng pananim. Hindi kinokopya sa datos ng TANIM ang mga production value nito.",
              url: "https://rsso04a.psa.gov.ph/sites/default/files/attachment-dir/Region04A-56_SR%20No.%202026-100_2025%20Crops%20Production%20in%20Quezon.pdf",
              terms: "Ayon sa source notes, CC BY 4.0 ang nilalaman ng website ng PSA maliban kung may ibang nakasaad.",
            },
            {
              name: "2010-2025 Strawberry Situationer: Province of Benguet",
              category: "Opisyal na pampublikong source: PSA Cordillera Administrative Region",
              use: "Kinukumpirma nito ang Strawberry bilang mahalagang fruit crop sa Benguet. Hindi kinokopya sa nabuong value ng TANIM ang mga production value.",
              url: "https://rssocar.psa.gov.ph/content/2010-2025-strawberry-situationer-province-benguet",
              terms: "Ayon sa source notes, CC BY 4.0 ang nilalaman ng website ng PSA maliban kung may ibang nakasaad.",
            },
            {
              name: "2025 First Quarter Other Crops Production Situation in Benguet",
              category: "Opisyal na pampublikong source: PSA Cordillera Administrative Region",
              use: "Kinukumpirma nito ang saklaw sa Benguet ng Strawberry, Lemon, at Chinese cabbage. Hindi kinokopya sa nabuong value ng TANIM ang mga production value.",
              url: "https://rssocar.psa.gov.ph/content/2025-first-quarter-other-crops-production-situation-benguet",
              terms: "Ayon sa source notes, CC BY 4.0 ang nilalaman ng website ng PSA maliban kung may ibang nakasaad.",
            },
            {
              name: "Situation of Selected High Value Crops of Benguet, January-June 2025",
              category: "Opisyal na pampublikong source: PSA Cordillera Administrative Region",
              use: "Kinukumpirma nito ang Chinese cabbage at sweet peas bilang mga panindang pananim sa Benguet. Hindi kinokopya sa nabuong value ng TANIM ang mga production value.",
              url: "https://rssocar.psa.gov.ph/content/situation-selected-high-value-crops-benguet-january-june-2025",
              terms: "Ayon sa source notes, CC BY 4.0 ang nilalaman ng website ng PSA maliban kung may ibang nakasaad.",
            },
            {
              name: "Plants of the World Online",
              category: "Reference database: Royal Botanic Gardens, Kew",
              use: "Kinonsulta para sa mga piling siyentipikong pangalan. Hindi sinasabi ng source notes na sinuri rito ang bawat pangalan sa registry.",
              url: "https://powo.science.kew.org/",
              terms: "Tingnan ang mga tuntunin ng Kew para sa paggamit ng database, ayon sa source notes.",
            },
            {
              name: "Anunsyo tungkol sa National Color-Coded Agricultural Guide (NCCAG) Map 2.0",
              category: "Opisyal na pampublikong source: Department of Agriculture",
              use: "Pangkalahatang sanggunian para sa magiging gabay sa kaangkupan ng pananim at lokasyon. Walang NCCAG o BSWM location-level layer na ginamit sa paggawa ng kasalukuyang synthetic suitability row.",
              url: "https://www.da.gov.ph/da-launches-updated-color-coded-agri-map-to-help-farmers-address-climate-vulnerability-and-boost-yield-income/",
              terms: "Ayon sa source notes, walang partikular na data license na nakasaad sa artikulo.",
            },
          ],
        },
        {
          kind: "callout",
          calloutKind: "data",
          title: "Synthetic na paraan ng TANIM",
          text: "Synthetic demo value ang mga nabuong presyo, lawak, ratio, at suitability label. May hiwalay na paraang TANIM para sa profile, reference area, supply context, at soil suitability. Hindi ito mga value na inilathala ng PSA, DA, Kew, PSGC Cloud, NCCAG, o BSWM.",
        },
      ],
    },
    ["/data", "/data/synthetic-data", "/data/geography", "/legal/copyright"],
  ),
  page(
    "/data/synthetic-data",
    "data",
    {
      title: "Synthetic Data",
      description: "Learn why TANIM uses generated demo numbers and what those numbers do not mean.",
      blocks: [
        {
          kind: "text",
          heading: "Why demo data is used",
          paragraphs: [
            "Complete agricultural data is not available for every TANIM crop, place, and planning period. The project therefore uses deterministic synthetic demo data for some prices, reference areas, supply context, and suitability labels.",
            "Synthetic values are created for the prototype. They are not exact government measurements. Public sources may guide crop names, geography, data shape, or broad context, but they did not publish each generated TANIM number.",
          ],
        },
        {
          kind: "list",
          heading: "What deterministic means",
          items: [
            "The generator uses a fixed seed and a named dataset version.",
            "The same inputs and dataset version produce the same demo values.",
            "Changed methods or inputs need a new dataset version instead of silent replacement.",
            "Generated agriculture data is separate from live weather data.",
          ],
        },
        {
          kind: "definition",
          term: "Current dataset",
          text: "The repository config names the demo dataset demo-2026-09-v4. Its metadata records synthetic data kinds, units, methods, periods, and source references.",
        },
        {
          kind: "callout",
          calloutKind: "important",
          title: "No false source claim",
          text: "TANIM does not claim that PSA, DA, BSWM, NCCAG, PAGASA, Kew, or another source published a generated TANIM number.",
        },
      ],
    },
    {
      title: "Synthetic na Datos",
      description: "Alamin kung bakit gumagamit ang TANIM ng nabuong demo number at kung ano ang hindi ibig sabihin ng mga ito.",
      blocks: [
        {
          kind: "text",
          heading: "Bakit gumagamit ng demo data",
          paragraphs: [
            "Walang kumpletong agricultural data para sa bawat pananim, lugar, at planning period ng TANIM. Kaya gumagamit ang proyekto ng deterministic na synthetic demo data para sa ilang presyo, reference area, konteksto ng supply, at suitability label.",
            "Para sa prototype ginawa ang synthetic na value. Hindi ito eksaktong sukat ng gobyerno. Maaaring gabay ang mga pampublikong source sa pangalan ng pananim, heograpiya, hugis ng datos, o pangkalahatang konteksto, pero hindi nila inilathala ang bawat nabuong numero ng TANIM.",
          ],
        },
        {
          kind: "list",
          heading: "Kahulugan ng deterministic",
          items: [
            "Gumagamit ang generator ng nakapirming seed at pinangalanang bersyon ng dataset.",
            "Pareho ang demo value kapag pareho ang input at bersyon ng dataset.",
            "Kailangan ng bagong bersyon ng dataset kapag nagbago ang paraan o input. Hindi ito dapat palihim na palitan.",
            "Hiwalay ang nabuong agricultural data sa live weather data.",
          ],
        },
        {
          kind: "definition",
          term: "Kasalukuyang dataset",
          text: "demo-2026-09-v4 ang pangalan ng demo dataset sa repository config. Itinatala ng metadata nito ang synthetic na uri ng datos, yunit, paraan, panahon, at mga sanggunian.",
        },
        {
          kind: "callout",
          calloutKind: "important",
          title: "Walang maling pag-angkin sa source",
          text: "Hindi sinasabi ng TANIM na PSA, DA, BSWM, NCCAG, PAGASA, Kew, o ibang source ang naglathala ng nabuong numero ng TANIM.",
        },
      ],
    },
    ["/data", "/data/sources", "/engine", "/limitations"],
  ),
  page(
    "/data/geography",
    "data",
    {
      title: "Geographic Coverage",
      description: "See the current supported areas and levels in the TANIM registry.",
      blocks: [
        {
          kind: "list",
          heading: "Current coverage",
          items: [
            "Area: Luzon, Philippines",
            "Levels: Region, Province, and Municipality or City",
            "The repository geography notes count 8 regions, 38 provinces, and 771 municipalities or cities.",
          ],
        },
        {
          kind: "definition",
          term: "Barangay",
          text: "Barangay-level product behavior and registry coverage are out of scope.",
        },
        {
          kind: "callout",
          calloutKind: "limitation",
          title: "Future areas",
          text: "Visayas and Mindanao may be considered for future expansion. TANIM does not present them as currently supported areas.",
        },
      ],
    },
    {
      title: "Saklaw na Heograpiya",
      description: "Tingnan ang kasalukuyang sinusuportahang lugar at antas sa TANIM registry.",
      blocks: [
        {
          kind: "list",
          heading: "Kasalukuyang saklaw",
          items: [
            "Lugar: Luzon, Pilipinas",
            "Mga antas: Region, Province, at Municipality or City",
            "Ayon sa geography notes ng repository, may 8 rehiyon, 38 lalawigan, at 771 munisipalidad o lungsod.",
          ],
        },
        {
          kind: "definition",
          term: "Barangay",
          text: "Hindi kasama sa kasalukuyang saklaw ang product behavior at registry coverage sa antas ng barangay.",
        },
        {
          kind: "callout",
          calloutKind: "limitation",
          title: "Mga lugar sa hinaharap",
          text: "Maaaring isaalang-alang ang Visayas at Mindanao para sa pagpapalawak sa hinaharap. Hindi ipinapakita ng TANIM na sinusuportahan na ang mga ito ngayon.",
        },
      ],
    },
    ["/data", "/data/sources", "/maps/supply", "/limitations"],
  ),
  page(
    "/limitations",
    "limitations",
    {
      title: "Limitations",
      description: "What the TANIM prototype can and cannot tell you today.",
      blocks: [
        {
          kind: "list",
          heading: "Current limits",
          items: [
            "Geography is limited to Luzon. Barangay detail is not supported.",
            "Some agriculture values are synthetic prototype data, not exact official measurements.",
            "Glut Risk uses prototype thresholds and a reference area. It is not a guaranteed market prediction.",
            "Soil suitability is contextual and may be synthetic. It is not a real soil survey in the current dataset.",
            "Live weather may need internet and may be unavailable. Weather is not used by the Phase 3 risk engine.",
            "The core Glut Risk calculation does not use machine learning.",
            "The current version includes account registration, sign-in, consent, the first-time demo, Farmer planting-plan management, Cooperative overview, and read-only crop and context utilities. Advanced Cooperative administration is not included. Live weather still needs internet and a reachable provider.",
          ],
        },
        {
          kind: "text",
          heading: "Use results with context",
          paragraphs: [
            "Use TANIM as planning support. Check the location, crop, period, reference, and data status shown with a result. Make farming and market decisions with your own judgment and local knowledge.",
          ],
        },
      ],
    },
    {
      title: "Mga Limitasyon",
      description: "Mga bagay na masasabi at hindi masasabi ng TANIM prototype sa kasalukuyan.",
      blocks: [
        {
          kind: "list",
          heading: "Kasalukuyang mga limitasyon",
          items: [
            "Sa Luzon lamang ang saklaw ng heograpiya. Hindi sinusuportahan ang detalye ng barangay.",
            "Synthetic prototype data ang ilang agricultural value, hindi eksaktong opisyal na sukat.",
            "Gumagamit ang Glut Risk ng prototype threshold at reference area. Hindi ito garantisadong prediksyon sa merkado.",
            "Konteksto ang soil suitability at maaaring synthetic. Hindi ito tunay na soil survey sa kasalukuyang dataset.",
            "Maaaring mangailangan ng internet ang live weather at maaaring hindi ito available. Hindi ginagamit ng Phase 3 risk engine ang weather.",
            "Hindi gumagamit ng machine learning ang pangunahing pagkukuwenta ng Glut Risk.",
            "May registration, sign-in, privacy consent, unang demo, pamamahala ng planting plan ng Farmer, Cooperative overview, at read-only crop at context utilities na ang TANIM. Hindi kasama ang advanced Cooperative administration. Kailangan pa rin ng internet at reachable provider para sa live weather.",
          ],
        },
        {
          kind: "text",
          heading: "Gamitin ang resulta kasama ang konteksto",
          paragraphs: [
            "Gamitin ang TANIM bilang pantulong sa pagpaplano. Suriin ang lugar, pananim, panahon, reference, at status ng datos na ipinapakita kasama ng resulta. Gamitin pa rin ang sarili mong paghatol at lokal na kaalaman sa mga pasya tungkol sa pagsasaka at merkado.",
          ],
        },
      ],
    },
    ["/engine", "/data/synthetic-data", "/data/geography", "/legal/terms"],
  ),
  page(
    "/help/faq",
    "help",
    {
      title: "Help and FAQ",
      description: "Answers about Glut Risk, synthetic data, weather, language, and supported places.",
      blocks: [
        {
          kind: "faq",
          items: [
            {
              question: "What is TANIM?",
              answer: "TANIM helps farmers and cooperatives compare registered crop plans with a reference level before planting decisions are final.",
            },
            {
              question: "Who can use TANIM?",
              answer: "Farmers and Cooperative users can register and sign in. New users read the Privacy Notice and accept the required service consent before registration.",
            },
            {
              question: "What does High Glut Risk mean?",
              answer: "The engine ratio is above 1.10 under the current prototype thresholds. It means planned area is high compared with the configured reference in that context.",
            },
            {
              question: "Does High risk mean the crop price will fall?",
              answer: "No. The engine compares planned area with a reference. It does not predict a guaranteed price change.",
            },
            {
              question: "Does Low risk guarantee profit?",
              answer: "No. Low is an indicator from the current supply calculation. It does not guarantee a sale or profit.",
            },
            {
              question: "Why is my crop comparison different after adding my area?",
              answer: "The comparison can show current pressure and a hypothetical result if the same proposed area is added to another crop. It is informational, not a profit or suitability ranking.",
            },
            {
              question: "Why is some data marked synthetic?",
              answer: "Complete agricultural data is not available for every crop, place, and period. Synthetic demo values let the prototype show a repeatable example without claiming that a public source published those exact numbers.",
            },
            {
              question: "Why is weather unavailable?",
              answer: "Live weather needs internet and a reachable service. TANIM uses an Open-Meteo adapter. The screen asks the user to Continue before the request and provides Retry when the service fails.",
            },
            {
              question: "Does weather affect Glut Risk?",
              answer: "No. The Phase 3 Glut Risk engine does not use weather.",
            },
            {
              question: "What areas does TANIM support?",
              answer: "The current scope is Luzon, with Region, Province, and Municipality or City levels.",
            },
            {
              question: "Does TANIM support barangays?",
              answer: "No. Barangay-level product behavior is out of scope.",
            },
            {
              question: "Can I use TANIM without internet?",
              answer: "The local crop, plan, and context features run on your computer with the local API and database. Live weather needs internet and a reachable provider.",
            },
            {
              question: "What happens to demo data?",
              answer: "The first-time demo shows sample Tomato and Eggplant scenarios. It explains the engine result, but it does not create or save a planting plan. Seeded accounts are available for local development.",
            },
            {
              question: "Can I change the language?",
              answer: "Yes. Use the language selector at the top of this site. Your choice is stored in this browser, and the site keeps you on the same page.",
            },
          ],
        },
      ],
    },
    {
      title: "Tulong at mga FAQ",
      description: "Mga sagot tungkol sa Glut Risk, synthetic na datos, weather, wika, at mga sinusuportahang lugar.",
      blocks: [
        {
          kind: "faq",
          items: [
            {
              question: "Ano ang TANIM?",
              answer: "Tinutulungan ng TANIM ang mga magsasaka at kooperatiba na ihambing ang mga rehistradong plano sa pananim sa batayang antas bago matapos ang pasya sa pagtatanim.",
            },
            {
              question: "Sino ang maaaring gumamit ng TANIM?",
              answer: "Maaaring gumawa ng account at mag-sign in ang mga magsasaka at gumagamit mula sa kooperatiba. Binabasa muna ng mga bagong user ang Privacy Notice at tinatanggap ang kinakailangang pahintulot para sa serbisyo.",
            },
            {
              question: "Ano ang ibig sabihin ng High Glut Risk?",
              answer: "Mas mataas sa 1.10 ang ratio ng engine sa ilalim ng kasalukuyang prototype thresholds. Ibig sabihin, mataas ang planong lawak kumpara sa configured na reference sa kontekstong iyon.",
            },
            {
              question: "Ibig bang sabihin ng High risk na bababa ang presyo ng pananim?",
              answer: "Hindi. Inihahambing ng engine ang planong lawak sa reference. Hindi nito tiyak na hinuhulaan ang pagbabago ng presyo.",
            },
            {
              question: "Ginagarantiya ba ng Low risk ang kita?",
              answer: "Hindi. Palatandaan ito mula sa kasalukuyang pagkukuwenta ng supply. Hindi nito ginagarantiya ang benta o kita.",
            },
            {
              question: "Bakit nagbabago ang crop comparison kapag idinagdag ko ang lawak ko?",
              answer: "Maaaring ipakita ng paghahambing ang kasalukuyang pressure at palagay na resulta kung idaragdag ang parehong iminungkahing lawak sa ibang pananim. Impormasyon lamang ito, hindi ranggo ng kita o kaangkupan.",
            },
            {
              question: "Bakit may markang synthetic ang ilang datos?",
              answer: "Walang kumpletong agricultural data para sa bawat pananim, lugar, at panahon. Nagbibigay-daan ang synthetic demo value sa prototype na magpakita ng paulit-ulit na halimbawa nang hindi inaangking galing sa pampublikong source ang eksaktong mga numerong iyon.",
            },
            {
              question: "Bakit hindi available ang weather?",
              answer: "Kailangan ng internet at reachable service para sa live weather. Gumagamit ang TANIM ng Open-Meteo adapter. Hinihingi ng screen ang Continue bago ang request at nagbibigay ng Retry kapag nabigo ang service.",
            },
            {
              question: "Nakaaapekto ba ang weather sa Glut Risk?",
              answer: "Hindi. Hindi ginagamit ng Phase 3 Glut Risk engine ang weather.",
            },
            {
              question: "Anong mga lugar ang sinusuportahan ng TANIM?",
              answer: "Luzon ang kasalukuyang saklaw, sa antas ng Region, Province, at Municipality or City.",
            },
            {
              question: "Sinusuportahan ba ng TANIM ang barangay?",
              answer: "Hindi. Hindi kasama sa saklaw ang product behavior sa antas ng barangay.",
            },
            {
              question: "Magagamit ko ba ang TANIM nang walang internet?",
              answer: "Gumagana sa computer mo ang lokal na crop, plan, at context feature kasama ang local API at database. Kailangan ng internet at reachable provider para sa live weather.",
            },
            {
              question: "Ano ang nangyayari sa demo data?",
              answer: "Ipinapakita sa unang demo ang mga halimbawang sitwasyon ng Tomato at Eggplant. Ipinapaliwanag nito ang resulta ng engine pero hindi ito gumagawa o nagse-save ng planong pananim. May mga seeded account para sa lokal na development.",
            },
            {
              question: "Mababago ko ba ang wika?",
              answer: "Oo. Gamitin ang language selector sa itaas ng site. Naka-save sa browser ang pinili mong wika at mananatili ka sa parehong pahina.",
            },
          ],
        },
      ],
    },
    ["/getting-started", "/engine", "/data/synthetic-data", "/maps/weather", "/legal/privacy"],
  ),
  page(
    "/legal/privacy",
    "ethics-legal",
    {
      title: "Privacy",
      description: "What the current repository can confirm about user data and consent.",
      blocks: [
        {
          kind: "text",
          heading: "Current privacy information",
          paragraphs: [
            "To create an account, TANIM stores a name, email address, and role. It stores the password as a secure hash. A Cooperative account may also include an organization name. The app offers Farmer and Cooperative roles.",
            "Before registration, the app asks for required service consent. The optional data-improvement choice is separate and starts as off. TANIM records these choices with the current Privacy Notice version.",
            "The app supports sign-in sessions that last seven days. A saved planting plan records its owner, crop, location, area, dates, and lifecycle status. Farmers can access only their own plans. This page does not promise a retention period or deletion guarantee.",
          ],
        },
        {
          kind: "list",
          heading: "What this page does not promise",
          items: [
            "A data retention period",
            "A deletion guarantee",
            "A third-party sharing policy",
            "A legal compliance conclusion",
          ],
        },
        {
          kind: "callout",
          calloutKind: "important",
          title: "Privacy details need an implementation check",
          text: "This page describes the current account, consent, plan ownership, and session flow. It does not promise a data-retention period, a deletion process, or a legal compliance result.",
        },
      ],
    },
    {
      title: "Privacy",
      description: "Mga bagay tungkol sa user data at consent na makukumpirma sa kasalukuyang repository.",
      blocks: [
        {
          kind: "text",
          heading: "Kasalukuyang impormasyon sa privacy",
          paragraphs: [
            "Para gumawa ng account, iniimbak ng TANIM ang pangalan, email address, at tungkulin. Iniimbak nito ang password bilang secure na hash. Maaaring idagdag sa Cooperative account ang pangalan ng organisasyon. May Farmer at Cooperative na tungkulin sa app.",
            "Bago magparehistro, hinihingi ng app ang kinakailangang pahintulot para sa serbisyo. Hiwalay ang opsyonal na pagpili para sa pagpapabuti ng datos at naka-off ito bilang default. Itinatala ng TANIM ang mga pagpiling ito kasama ang bersyon ng Privacy Notice.",
            "May sign-in session ang app na tumatagal nang pitong araw. Ang saved planting plan ay may owner, pananim, lugar, lawak, petsa, at lifecycle status. Sariling plano lamang ng Farmer ang maaaring ma-access. Hindi nangangako ang pahinang ito ng panahon ng pag-iingat o garantiyang mabubura ang datos.",
          ],
        },
        {
          kind: "list",
          heading: "Mga hindi ipinapangako ng pahinang ito",
          items: [
            "Panahon ng pag-iingat ng datos",
            "Garantiyang mabubura ang datos",
            "Patakaran sa pagbabahagi sa third party",
            "Pagsunod sa batas",
          ],
        },
        {
          kind: "callout",
          calloutKind: "important",
          title: "Kailangang suriin ang pagpapatupad ng privacy",
          text: "Inilalarawan ng pahinang ito ang kasalukuyang daloy ng account, consent, pagmamay-ari ng plano, at session. Hindi ito nangangako ng panahon ng pag-iingat ng datos, proseso ng pagbura, o resulta tungkol sa pagsunod sa batas.",
        },
      ],
    },
    ["/legal/ethics", "/legal/terms", "/data/synthetic-data", "/help/faq"],
  ),
  page(
    "/legal/ethics",
    "ethics-legal",
    {
      title: "Ethics",
      description: "The practical principles TANIM follows when showing crop and supply information.",
      blocks: [
        {
          kind: "list",
          heading: "How TANIM should support people",
          items: [
            "Support farmer judgment. Do not replace it.",
            "Present risk levels as indicators, not guarantees.",
            "Label generated values as TANIM synthetic demo data.",
            "Show when a reference or other input is missing. Do not hide uncertainty.",
            "Keep supply pressure and crop suitability as separate ideas.",
            "Do not imply government endorsement unless an official record supports that claim.",
            "Avoid unnecessary exposure of private user information.",
            "Use useful aggregation for cooperative information where possible, and explain who can see each view after it is implemented.",
          ],
        },
        {
          kind: "text",
          heading: "A result is a prompt for discussion",
          paragraphs: [
            "A Low, Moderate, or High result describes one calculation and its data context. Farmers and cooperatives can combine it with local knowledge, crop conditions, and their own plans.",
          ],
        },
      ],
    },
    {
      title: "Etika",
      description: "Mga praktikal na prinsipyong sinusunod ng TANIM sa pagpapakita ng impormasyon tungkol sa pananim at supply.",
      blocks: [
        {
          kind: "list",
          heading: "Paano dapat sumuporta ang TANIM sa mga tao",
          items: [
            "Suportahan ang paghatol ng magsasaka. Huwag itong palitan.",
            "Ipakita ang risk level bilang palatandaan, hindi garantiya.",
            "Markahan bilang TANIM synthetic demo data ang mga nabuong value.",
            "Ipakita kapag nawawala ang reference o ibang input. Huwag itago ang kawalan ng katiyakan.",
            "Paghiwalayin ang pressure sa supply at kaangkupan ng pananim.",
            "Huwag magpahiwatig ng pag-endorso ng gobyerno kung walang opisyal na batayan.",
            "Iwasan ang hindi kailangang paglalantad ng pribadong impormasyon ng user.",
            "Gumamit ng kapaki-pakinabang na pinagsama-samang impormasyon para sa kooperatiba kung maaari, at ipaliwanag kung sino ang makakakita sa bawat view kapag naipatupad na ito.",
          ],
        },
        {
          kind: "text",
          heading: "Panimula sa usapan ang resulta",
          paragraphs: [
            "Inilalarawan ng Low, Moderate, o High na resulta ang isang pagkukuwenta at konteksto ng datos nito. Maaari itong samahan ng mga magsasaka at kooperatiba ng lokal na kaalaman, kalagayan ng pananim, at sarili nilang plano.",
          ],
        },
      ],
    },
    ["/engine/risk-levels", "/data/synthetic-data", "/legal/privacy", "/legal/terms"],
  ),
  page(
    "/legal/terms",
    "ethics-legal",
    {
      title: "Terms",
      description: "A short explanation of the limits of this TANIM hackathon prototype.",
      blocks: [
        {
          kind: "text",
          heading: "TANIM is a prototype",
          paragraphs: [
            "TANIM is a hackathon prototype for planning support. Information may include prototype or synthetic data. The service and its results do not promise a particular market outcome.",
            "You remain responsible for farming, planting, and market decisions. Review the assumptions, reference level, and data status before using a result.",
            "Local service availability is not guaranteed. Some features, such as live weather, may need internet and may be unavailable.",
          ],
        },
        {
          kind: "callout",
          calloutKind: "note",
          title: "Plain-language summary",
          text: "Use TANIM to support a decision. Do not treat it as a promise of price, yield, sale, or profit.",
        },
      ],
    },
    {
      title: "Mga Tuntunin",
      description: "Maikling paliwanag sa mga limitasyon ng TANIM hackathon prototype na ito.",
      blocks: [
        {
          kind: "text",
          heading: "Prototype ang TANIM",
          paragraphs: [
            "Hackathon prototype ang TANIM para sa pantulong sa pagpaplano. Maaaring may prototype o synthetic na datos ang impormasyon. Hindi nangangako ang serbisyo at mga resulta nito ng partikular na mangyayari sa merkado.",
            "Ikaw pa rin ang responsable sa mga pasya sa pagsasaka, pagtatanim, at merkado. Suriin ang mga palagay, reference level, at status ng datos bago gamitin ang resulta.",
            "Hindi ginagarantiya ang availability ng lokal na serbisyo. Maaaring mangailangan ng internet ang ilang feature gaya ng live weather at maaaring hindi ito available.",
          ],
        },
        {
          kind: "callout",
          calloutKind: "note",
          title: "Payak na buod",
          text: "Gamitin ang TANIM bilang suporta sa pasya. Huwag ituring itong pangako sa presyo, ani, benta, o kita.",
        },
      ],
    },
    ["/limitations", "/legal/ethics", "/legal/privacy", "/legal/copyright"],
  ),
  page(
    "/legal/copyright",
    "ethics-legal",
    {
      title: "Copyright and Licenses",
      description: "Where to find repository, dependency, source, and synthetic data terms.",
      blocks: [
        {
          kind: "text",
          heading: "TANIM project terms",
          paragraphs: [
            "This repository version does not include a project LICENSE file or a file that names the TANIM copyright owner. This page does not guess an owner, grant a software license, or state reuse terms that the repository does not record.",
            "Before reusing TANIM code, ask the project maintainers for the applicable terms. Review the repository again for a license file when one is added.",
          ],
        },
        {
          kind: "list",
          heading: "Third-party software and data",
          items: [
            "JavaScript dependencies are listed in the workspace package manifests and package-lock.json.",
            "Python dependencies are listed in pyproject.toml.",
            "Each third-party package keeps its own license terms. This project does not provide a complete dependency license catalogue on this page.",
            "Third-party data and source terms are summarized in Data Sources. Where the repository records no specific license, this page makes no license claim.",
          ],
        },
        {
          kind: "definition",
          term: "Synthetic dataset status",
          text: "Generated TANIM demo records are prototype data with recorded methods and versions. They are not values published by the public sources listed for context.",
        },
      ],
    },
    {
      title: "Copyright at mga Lisensya",
      description: "Kung saan makikita ang mga tuntunin para sa repository, dependency, source, at synthetic data.",
      blocks: [
        {
          kind: "text",
          heading: "Mga tuntunin ng TANIM project",
          paragraphs: [
            "Walang project LICENSE file o file na nagsasaad ng may-ari ng copyright ng TANIM sa bersyong ito ng repository. Hindi nanghuhula ang pahinang ito ng may-ari, nagbibigay ng software license, o nagsasaad ng tuntunin sa paggamit na wala sa repository.",
            "Bago gamitin muli ang TANIM code, hingin sa project maintainer ang naaangkop na mga tuntunin. Suriin muli ang repository kapag may idinagdag na license file.",
          ],
        },
        {
          kind: "list",
          heading: "Third-party software at datos",
          items: [
            "Nasa workspace package manifest at package-lock.json ang JavaScript dependency.",
            "Nasa pyproject.toml ang Python dependency.",
            "May sariling license terms ang bawat third-party package. Walang kumpletong talaan ng license ng dependency sa pahinang ito.",
            "Nasa Data Sources ang buod ng tuntunin para sa third-party data at source. Kapag walang partikular na lisensyang naitala sa repository, wala ring inaangking lisensya rito.",
          ],
        },
        {
          kind: "definition",
          term: "Katayuan ng synthetic dataset",
          text: "Prototype data na may nakatalang paraan at bersyon ang mga nabuong TANIM demo record. Hindi ito mga value na inilathala ng mga pampublikong source na nakalista bilang konteksto.",
        },
      ],
    },
    ["/data/sources", "/data/synthetic-data", "/legal/terms", "/legal/ethics"],
  ),
];

export const notFoundCopy: Record<"en" | "tl", PageCopy> = {
  en: {
    title: "Page not found",
    description: "This documentation page is not available.",
    blocks: [
      {
        kind: "text",
        paragraphs: [
          "The address may be old or typed incorrectly. Start from Introduction or open Getting Started.",
        ],
      },
    ],
  },
  tl: {
    title: "Hindi makita ang pahina",
    description: "Hindi available ang pahinang ito ng dokumentasyon.",
    blocks: [
      {
        kind: "text",
        paragraphs: [
          "Maaaring luma o mali ang address. Magsimula sa Panimula o buksan ang Pagsisimula.",
        ],
      },
    ],
  },
};
