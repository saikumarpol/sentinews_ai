"use client";

import {
  FormEvent,
  ReactNode,
  useEffect,
  useState,
} from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";


// ============================================================
// TYPES
// ============================================================

type Source = {
  title?: string;
  url?: string;
  content?: string;
  domain?: string;
  quality?: string;
};

type MarketData = {
  symbol?: string;

  quote?: {
    last?: number;
    previousClose?: number;
    change?: number;
    changePercent?: number;
    open?: number;
    high?: number;
    low?: number;
    volume?: number;
    date?: string;
  };

  freshness?: {
    label?: string;
    status?: string;
    businessDaysOld?: number;
  };

  dataSource?: string;
  dataType?: string;
  exchange?: string;
};

type ResearchResponse = {
  query: string;

  type?: string;

  company?: string;

  companies?: string[];

  sector?: string;

  answer?: string;

  results?: Source[];

  searchQueries?: string[];

  evidenceLevel?: string;

  evidenceStats?: {
    totalSources?: number;
    primarySources?: number;
    trustedFinancialSources?: number;
  };

  marketData?: MarketData[];

  disclaimer?: string;

  restricted?: boolean;

  model?: string;
};

type ChatMessage = {
  id: string;

  role: "user" | "assistant";

  content: string;

  response?: ResearchResponse;

  createdAt: number;
};

type ResearchSession = {
  id: string;

  title: string;

  createdAt: number;

  updatedAt: number;

  messages: ChatMessage[];
};


// ============================================================
// HELPERS
// ============================================================

function makeId() {
  return `${Date.now()}-${Math.random()
    .toString(36)
    .slice(2, 10)}`;
}


function formatNumber(
  value: unknown,
  digits = 2,
) {
  if (
    typeof value !== "number" ||
    Number.isNaN(value)
  ) {
    return "—";
  }

  return value.toLocaleString(
    "en-IN",
    {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    },
  );
}


function formatDate(
  value?: string,
) {
  if (!value) return "—";

  const date = new Date(
    `${value}T00:00:00`,
  );

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString(
    "en-IN",
    {
      day: "numeric",
      month: "short",
      year: "numeric",
    },
  );
}


function formatTime(
  timestamp: number,
) {
  return new Date(
    timestamp,
  ).toLocaleTimeString(
    "en-IN",
    {
      hour: "2-digit",
      minute: "2-digit",
    },
  );
}


function getEvidenceLabel(
  level?: string,
) {
  switch (level) {
    case "strong":
      return "Strong evidence";

    case "moderate":
      return "Moderate evidence";

    case "limited":
      return "Limited evidence";

    default:
      return "Insufficient evidence";
  }
}


function getQualityLabel(
  quality?: string,
) {
  switch (quality) {
    case "primary":
      return "Primary source";

    case "trusted_financial":
      return "Financial source";

    default:
      return "Web source";
  }
}


// ============================================================
// INLINE MARKDOWN
// ============================================================

function renderInline(
  text: string,
  sources: Source[],
): ReactNode[] {

  const parts = text.split(
    /(\[\d+\]|\*\*[^*]+\*\*)/g,
  );

  return parts.map(
    (part, index) => {

      // Citation
      const citation =
        part.match(
          /^\[(\d+)\]$/,
        );

      if (citation) {

        const number =
          Number(citation[1]);

        const source =
          sources[number - 1];

        if (!source) {
          return (
            <span key={index}>
              {part}
            </span>
          );
        }

        return (
          <a
            key={index}
            href={
              source.url || "#"
            }
            target="_blank"
            rel="noreferrer"
            className="mx-1 inline-flex items-center rounded-md bg-white/10 px-1.5 py-0.5 text-[10px] font-semibold text-white hover:bg-white/20"
            title={
              source.title ||
              `Source ${number}`
            }
          >
            {number}
          </a>
        );
      }


      // Bold
      if (
        part.startsWith("**") &&
        part.endsWith("**")
      ) {

        return (
          <strong
            key={index}
            className="font-semibold text-white"
          >
            {renderInline(
              part.slice(2, -2),
              sources,
            )}
          </strong>
        );
      }


      return (
        <span key={index}>
          {part}
        </span>
      );
    },
  );
}


// ============================================================
// ANSWER RENDERER
// ============================================================

function renderAnswer(
  answer: string,
  sources: Source[],
) {

  const lines =
    answer.split("\n");

  const output: ReactNode[] = [];

  let index = 0;


  while (
    index < lines.length
  ) {

    const line =
      lines[index].trim();


    if (!line) {
      index++;
      continue;
    }


    // ========================================================
    // TABLE
    // ========================================================

    if (
      line.includes("|") &&
      index + 1 < lines.length &&
      lines[index + 1].includes("---")
    ) {

      const headers =
        line
          .split("|")
          .map((x) => x.trim())
          .filter(Boolean);

      index += 2;

      const rows: string[][] =
        [];

      while (
        index < lines.length &&
        lines[index].includes("|")
      ) {

        rows.push(
          lines[index]
            .split("|")
            .map((x) => x.trim())
            .filter(Boolean),
        );

        index++;
      }


      output.push(
        <div
          key={`table-${index}`}
          className="my-5 overflow-hidden rounded-xl border border-white/10"
        >
          <div className="overflow-x-auto">

            <table className="w-full text-sm">

              <thead className="bg-white/[0.04]">

                <tr>

                  {headers.map(
                    (header) => (
                      <th
                        key={header}
                        className="px-4 py-3 text-left font-medium text-white/60"
                      >
                        {renderInline(
                          header,
                          sources,
                        )}
                      </th>
                    ),
                  )}

                </tr>

              </thead>


              <tbody>

                {rows.map(
                  (row, rowIndex) => (

                    <tr
                      key={rowIndex}
                      className="border-t border-white/5"
                    >

                      {row.map(
                        (
                          cell,
                          cellIndex,
                        ) => (

                          <td
                            key={cellIndex}
                            className="px-4 py-3 text-white/75"
                          >
                            {renderInline(
                              cell,
                              sources,
                            )}
                          </td>

                        ),
                      )}

                    </tr>

                  ),
                )}

              </tbody>

            </table>

          </div>
        </div>,
      );

      continue;
    }


    // ========================================================
    // HEADINGS
    // ========================================================

    if (
      line.startsWith("### ")
    ) {

      output.push(
        <h3
          key={index}
          className="mt-8 mb-3 text-lg font-semibold text-white"
        >
          {renderInline(
            line.slice(4),
            sources,
          )}
        </h3>,
      );

      index++;

      continue;
    }


    if (
      line.startsWith("## ")
    ) {

      output.push(
        <h2
          key={index}
          className="mt-8 mb-3 text-xl font-semibold text-white"
        >
          {renderInline(
            line.slice(3),
            sources,
          )}
        </h2>,
      );

      index++;

      continue;
    }


    // ========================================================
    // BULLET LIST
    // ========================================================

    if (
      line.startsWith("- ") ||
      line.startsWith("* ")
    ) {

      const items: string[] =
        [];

      while (
        index < lines.length &&
        (
          lines[index]
            .trim()
            .startsWith("- ") ||
          lines[index]
            .trim()
            .startsWith("* ")
        )
      ) {

        items.push(
          lines[index]
            .trim()
            .slice(2),
        );

        index++;
      }


      output.push(
        <ul
          key={`list-${index}`}
          className="my-4 space-y-2 pl-5 text-white/75"
        >

          {items.map(
            (item, itemIndex) => (

              <li
                key={itemIndex}
                className="list-disc leading-7"
              >
                {renderInline(
                  item,
                  sources,
                )}
              </li>

            ),
          )}

        </ul>,
      );

      continue;
    }


    // ========================================================
    // NUMBERED LIST
    // ========================================================

    if (
      /^\d+\.\s/.test(line)
    ) {

      const items: string[] =
        [];

      while (
        index < lines.length &&
        /^\d+\.\s/.test(
          lines[index].trim(),
        )
      ) {

        items.push(
          lines[index]
            .trim()
            .replace(
              /^\d+\.\s/,
              "",
            ),
        );

        index++;
      }


      output.push(
        <ol
          key={`ordered-${index}`}
          className="my-4 space-y-2 pl-5 text-white/75"
        >

          {items.map(
            (item, itemIndex) => (

              <li
                key={itemIndex}
                className="list-decimal leading-7"
              >
                {renderInline(
                  item,
                  sources,
                )}
              </li>

            ),
          )}

        </ol>,
      );

      continue;
    }


    // ========================================================
    // QUOTE
    // ========================================================

    if (
      line.startsWith("> ")
    ) {

      output.push(
        <blockquote
          key={index}
          className="my-4 border-l-2 border-white/20 pl-4 text-white/50"
        >
          {renderInline(
            line.slice(2),
            sources,
          )}
        </blockquote>,
      );

      index++;

      continue;
    }


    // ========================================================
    // NORMAL PARAGRAPH
    // ========================================================

    output.push(
      <p
        key={index}
        className="my-4 leading-7 text-white/75"
      >
        {renderInline(
          line,
          sources,
        )}
      </p>,
    );

    index++;
  }


  return output;
}


// ============================================================
// SOURCE COMPONENT
// ============================================================

function SourcesSection({
  response,
}: {
  response: ResearchResponse;
}) {

  const sources =
    response.results || [];

  if (!sources.length) {
    return null;
  }


  return (
    <section className="mt-8">

      <div className="mb-4 flex items-center gap-2">

        <h3 className="text-sm font-semibold">
          Sources
        </h3>

        <span className="rounded bg-white/[0.06] px-1.5 py-0.5 text-[9px] text-white/35">
          {sources.length}
        </span>

      </div>


      <div className="space-y-3">

        {sources.map(
          (source, index) => (

            <a
              key={`${source.url}-${index}`}
              href={
                source.url || "#"
              }
              target="_blank"
              rel="noreferrer"
              className="group block rounded-xl border border-white/10 bg-white/[0.02] p-4 transition hover:border-white/20 hover:bg-white/[0.04]"
            >

              <div className="flex gap-3">

                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-white/[0.06] text-xs text-white/50">
                  {index + 1}
                </div>


                <div className="min-w-0">

                  <div className="text-sm font-medium text-white/80 group-hover:text-white">
                    {source.title ||
                      "Untitled source"}
                  </div>


                  <div className="mt-1 flex flex-wrap items-center gap-2">

                    <span className="text-[10px] text-white/25">
                      {source.domain}
                    </span>

                    <span className="rounded-full bg-white/[0.05] px-2 py-0.5 text-[9px] text-white/35">
                      {getQualityLabel(
                        source.quality,
                      )}
                    </span>

                  </div>


                  <p className="mt-3 line-clamp-3 text-xs leading-5 text-white/35">
                    {source.content}
                  </p>

                </div>

              </div>

            </a>

          ),
        )}

      </div>

    </section>
  );
}


// ============================================================
// MARKET SECTION
// ============================================================

function MarketSection({
  response,
}: {
  response: ResearchResponse;
}) {

  const data =
    response.marketData || [];

  if (!data.length) {
    return null;
  }


  return (
    <section className="mt-8">

      <div className="mb-4">

        <h3 className="text-sm font-semibold">
          Market context
        </h3>

        <p className="mt-1 text-xs text-white/30">
          Structured market data
        </p>

      </div>


      <div className="grid gap-3 md:grid-cols-2">

        {data.map(
          (item) => {

            const quote =
              item.quote || {};

            const percent =
              quote.changePercent;

            const change =
              quote.change;

            const positive =
              typeof percent ===
                "number" &&
              percent >= 0;


            return (
              <div
                key={item.symbol}
                className="rounded-xl border border-white/10 bg-white/[0.025] p-5"
              >

                <div className="flex items-start justify-between">

                  <div>

                    <div className="text-sm font-semibold">
                      {item.symbol}
                    </div>

                    <div className="mt-1 text-[10px] uppercase tracking-wider text-white/30">
                      {item.exchange}
                      {" · "}
                      {item.dataType}
                    </div>

                  </div>


                  <div className="rounded-full bg-white/[0.05] px-2 py-1 text-[9px] text-white/35">
                    {item.freshness?.label ||
                      "Data freshness unknown"}
                  </div>

                </div>


                <div className="mt-5">

                  <div className="text-2xl font-semibold">
                    ₹
                    {formatNumber(
                      quote.last,
                    )}
                  </div>


                  <div
                    className={
                      `mt-1 text-sm ${
                        positive
                          ? "text-emerald-300"
                          : "text-red-300"
                      }`
                    }
                  >

                    {typeof change ===
                    "number"
                      ? `${
                          change >= 0
                            ? "+"
                            : ""
                        }₹${formatNumber(
                          change,
                        )}`
                      : "—"}

                    {" "}

                    {typeof percent ===
                    "number"
                      ? `(${
                          percent >= 0
                            ? "+"
                            : ""
                        }${formatNumber(
                          percent,
                        )}%)`
                      : ""}

                  </div>

                </div>


                <div className="mt-5 grid grid-cols-2 gap-3 border-t border-white/5 pt-4">

                  <div>

                    <div className="text-[10px] text-white/25">
                      As of
                    </div>

                    <div className="mt-1 text-xs text-white/60">
                      {formatDate(
                        quote.date,
                      )}
                    </div>

                  </div>


                  <div>

                    <div className="text-[10px] text-white/25">
                      Volume
                    </div>

                    <div className="mt-1 text-xs text-white/60">
                      {formatNumber(
                        quote.volume,
                        0,
                      )}
                    </div>

                  </div>

                </div>

              </div>
            );
          },
        )}

      </div>


      <div className="mt-3 text-[10px] leading-5 text-white/25">
        Structured stock data is EOD.
        Current-session information, when
        available, is explicitly identified
        as web-reported.
      </div>

    </section>
  );
}


// ============================================================
// EVIDENCE
// ============================================================

function EvidenceSection({
  response,
}: {
  response: ResearchResponse;
}) {

  const stats =
    response.evidenceStats;

  return (
    <section className="mt-8 rounded-xl border border-white/10 bg-white/[0.02] p-5">

      <div className="flex items-start justify-between">

        <div>

          <div className="text-xs text-white/35">
            Research evidence
          </div>

          <div className="mt-1 text-sm font-medium">
            {getEvidenceLabel(
              response.evidenceLevel,
            )}
          </div>

          <div className="mt-2 text-xs text-white/30">

            {stats?.primarySources || 0}
            {" primary · "}

            {stats?.trustedFinancialSources || 0}
            {" financial · "}

            {stats?.totalSources || 0}
            {" total"}

          </div>

        </div>


        <div className="text-right">

          <div className="text-2xl font-semibold">
            {stats?.totalSources || 0}
          </div>

          <div className="text-[9px] uppercase tracking-wider text-white/25">
            sources
          </div>

        </div>

      </div>

    </section>
  );
}


// ============================================================
// ASSISTANT MESSAGE
// ============================================================

function AssistantMessage({
  message,
}: {
  message: ChatMessage;
}) {

  const response =
    message.response;

  return (
    <div className="mt-8">

      <div className="flex items-center gap-3">

        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-xs font-bold text-black">
          S
        </div>

        <div>

          <div className="text-sm font-medium">
            SentiNews
          </div>

          <div className="text-[10px] text-white/25">
            Research model ·{" "}
            {formatTime(
              message.createdAt,
            )}
          </div>

        </div>

      </div>


      <div className="mt-2 text-[15px]">

        {renderAnswer(
          message.content,
          response?.results || [],
        )}

      </div>


      {response && (
        <>

          <MarketSection
            response={response}
          />

          <EvidenceSection
            response={response}
          />

          <SourcesSection
            response={response}
          />

        </>
      )}

    </div>
  );
}


// ============================================================
// MAIN
// ============================================================

export default function Home() {

  const [
    sessions,
    setSessions,
  ] = useState<ResearchSession[]>(
    [],
  );


  const [
    activeSessionId,
    setActiveSessionId,
  ] = useState<string | null>(
    null,
  );


  const [
    query,
    setQuery,
  ] = useState("");


  const [
    loading,
    setLoading,
  ] = useState(false);


  const [
    error,
    setError,
  ] = useState("");


  // ==========================================================
  // LOAD SESSIONS
  // ==========================================================

  useEffect(() => {

    try {

      const saved =
        localStorage.getItem(
          "sentinews-sessions",
        );

      if (!saved) {
        return;
      }

      const parsed =
        JSON.parse(saved);

      if (
        Array.isArray(parsed)
      ) {

        setSessions(parsed);

      }

    } catch {

      console.warn(
        "Unable to load SentiNews history.",
      );

    }

  }, []);


  // ==========================================================
  // SAVE SESSIONS
  // ==========================================================

  useEffect(() => {

    if (!sessions.length) {
      return;
    }

    try {

      localStorage.setItem(
        "sentinews-sessions",
        JSON.stringify(
          sessions,
        ),
      );

    } catch {

      console.warn(
        "Unable to save SentiNews history.",
      );

    }

  }, [sessions]);


  const activeSession =
    sessions.find(
      (session) =>
        session.id ===
        activeSessionId,
    ) || null;


  // ==========================================================
  // NEW RESEARCH
  // ==========================================================

  const newResearch = () => {

    setActiveSessionId(
      null,
    );

    setQuery("");

    setError("");

    setLoading(false);

  };


  // ==========================================================
  // DELETE ALL HISTORY
  // ==========================================================

  const clearHistory = () => {

    const confirmed =
      window.confirm(
        "Clear all recent research?",
      );

    if (!confirmed) {
      return;
    }

    setSessions([]);

    setActiveSessionId(
      null,
    );

    localStorage.removeItem(
      "sentinews-sessions",
    );

  };


  // ==========================================================
  // DELETE ONE SESSION
  // ==========================================================

  const deleteSession = (
    sessionId: string,
  ) => {

    setSessions(
      (previous) =>
        previous.filter(
          (session) =>
            session.id !==
            sessionId,
        ),
    );

    if (
      activeSessionId ===
      sessionId
    ) {

      setActiveSessionId(
        null,
      );

    }

  };


  // ==========================================================
  // SUBMIT
  // ==========================================================

  const submitResearch = async (
    event?: FormEvent,
    directQuestion?: string,
  ) => {

    event?.preventDefault();

    const question =
      (
        directQuestion ??
        query
      ).trim();

    if (
      !question ||
      loading
    ) {
      return;
    }


    setQuery("");

    setError("");

    setLoading(true);


    let sessionId =
      activeSessionId;


    // --------------------------------------------------------
    // CREATE NEW SESSION
    // --------------------------------------------------------

    if (!sessionId) {

      sessionId = makeId();

      const newSession:
        ResearchSession = {

        id: sessionId,

        title:
          question.length > 60
            ? `${question.slice(
                0,
                60,
              )}...`
            : question,

        createdAt:
          Date.now(),

        updatedAt:
          Date.now(),

        messages: [],
      };


      setSessions(
        (previous) => [
          newSession,
          ...previous,
        ],
      );


      setActiveSessionId(
        sessionId,
      );

    }


    // --------------------------------------------------------
    // GET CURRENT SESSION
    // --------------------------------------------------------

    const currentSession =
      sessions.find(
        (session) =>
          session.id ===
          sessionId,
      );


    const existingMessages =
      currentSession?.messages ||
      [];


    // --------------------------------------------------------
    // USER MESSAGE
    // --------------------------------------------------------

    const userMessage:
      ChatMessage = {

      id: makeId(),

      role: "user",

      content: question,

      createdAt: Date.now(),
    };


    // Optimistically add user message.
    setSessions(
      (previous) =>
        previous.map(
          (session) =>
            session.id ===
            sessionId
              ? {
                  ...session,
                  updatedAt:
                    Date.now(),
                  messages: [
                    ...session.messages,
                    userMessage,
                  ],
                }
              : session,
        ),
    );


    try {

      // ------------------------------------------------------
      // CONVERSATION HISTORY
      // ------------------------------------------------------

      const history =
        [
          ...existingMessages,
          userMessage,
        ]
          .slice(-10)
          .map(
            (message) => ({
              role:
                message.role,
              content:
                message.content,
            }),
          );


      const response =
        await fetch(
          `${API_URL}/api/ask`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({
              query: question,
              history,
            }),
          },
        );


      const data =
        await response.json();


      if (!response.ok) {

        const detail =
          typeof data.detail ===
          "string"
            ? data.detail
            : "Research request failed.";

        throw new Error(
          detail,
        );

      }


      // ------------------------------------------------------
      // ASSISTANT MESSAGE
      // ------------------------------------------------------

      const assistantMessage:
        ChatMessage = {

        id: makeId(),

        role: "assistant",

        content:
          data.answer || "",

        response: data,

        createdAt:
          Date.now(),
      };


      setSessions(
        (previous) =>
          previous.map(
            (session) =>
              session.id ===
              sessionId
                ? {
                    ...session,
                    updatedAt:
                      Date.now(),
                    messages: [
                      ...session.messages,
                      assistantMessage,
                    ],
                  }
                : session,
          ),
      );

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Unable to complete research.",
      );

    } finally {

      setLoading(false);

    }

  };


  // ==========================================================
  // SUGGESTIONS
  // ==========================================================

  const suggestions = [
    "What happened in today's Indian market?",
    "Why did TCS move recently?",
    "Compare TCS and Infosys",
    "Explain PE ratio",
  ];


  // ==========================================================
  // EMPTY STATE
  // ==========================================================

  const showEmpty =
    !activeSession &&
    !loading;


  return (
    <main className="min-h-screen bg-[#090a0b] text-white">

      <div className="flex min-h-screen">


        {/* ================================================== */}
        {/* SIDEBAR */}
        {/* ================================================== */}

        <aside className="hidden w-[260px] shrink-0 border-r border-white/10 bg-[#0c0d0e] lg:block">

          <div className="sticky top-0 flex h-screen flex-col">

            {/* BRAND */}

            <div className="flex items-center gap-3 border-b border-white/10 px-5 py-5">

              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white text-sm font-bold text-black">
                S
              </div>

              <div>

                <div className="text-sm font-semibold">
                  SentiNews
                </div>

                <div className="text-[11px] text-white/35">
                  Market intelligence
                </div>

              </div>

            </div>


            {/* NEW */}

            <div className="p-4">

              <button
                onClick={newResearch}
                className="flex w-full items-center gap-3 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-left text-sm transition hover:bg-white/[0.07]"
              >

                <span className="text-lg">
                  +
                </span>

                New research

              </button>

            </div>


            {/* RESEARCH */}

            <div className="px-5">

              <div className="mb-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/30">
                Research
              </div>


              <button
                onClick={() =>
                  submitResearch(
                    undefined,
                    "What happened in today's Indian market?",
                  )
                }
                className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-sm text-white/60 hover:bg-white/[0.04] hover:text-white"
              >

                <span>
                  ⌕
                </span>

                Explore market

              </button>

            </div>


            {/* HISTORY */}

            <div className="mt-7 min-h-0 flex-1 overflow-y-auto px-4">

              <div className="mb-3 flex items-center justify-between px-1">

                <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/30">
                  Recent research
                </div>


                {sessions.length > 0 && (

                  <button
                    onClick={
                      clearHistory
                    }
                    className="text-[9px] text-white/20 hover:text-white/60"
                  >
                    Clear
                  </button>

                )}

              </div>


              {sessions.length === 0 ? (

                <p className="px-1 text-xs leading-5 text-white/25">
                  Your research sessions
                  will appear here.
                </p>

              ) : (

                <div className="space-y-1">

                  {sessions.map(
                    (session) => (

                      <div
                        key={session.id}
                        className={`group flex items-start gap-1 rounded-lg transition ${
                          activeSessionId ===
                          session.id
                            ? "bg-white/[0.06]"
                            : "hover:bg-white/[0.04]"
                        }`}
                      >

                        <button
                          onClick={() => {

                            // IMPORTANT:
                            // This only opens saved data.
                            // It does NOT call the API.

                            setActiveSessionId(
                              session.id,
                            );

                            setQuery("");

                            setError("");

                          }}
                          className="min-w-0 flex-1 px-2 py-3 text-left"
                        >

                          <div className="truncate text-xs text-white/70">
                            {session.title}
                          </div>


                          <div className="mt-1 flex items-center gap-2 text-[9px] uppercase tracking-wider text-white/25">

                            <span>
                              {session.messages.filter(
                                (message) =>
                                  message.role ===
                                  "user",
                              ).length}{" "}
                              questions
                            </span>

                            <span>
                              ·
                            </span>

                            <span>
                              {formatTime(
                                session.updatedAt,
                              )}
                            </span>

                          </div>

                        </button>


                        <button
                          onClick={() =>
                            deleteSession(
                              session.id,
                            )
                          }
                          className="mr-1 mt-2 hidden rounded p-1 text-xs text-white/20 hover:text-white/70 group-hover:block"
                          title="Delete research"
                        >
                          ×
                        </button>

                      </div>

                    ),
                  )}

                </div>

              )}

            </div>


            {/* FOOTER */}

            <div className="border-t border-white/10 p-5">

              <p className="text-[10px] leading-4 text-white/25">
                Informational and educational
                market research only.
                <br />
                Not personalized investment advice.
              </p>

            </div>

          </div>

        </aside>


        {/* ================================================== */}
        {/* MAIN */}
        {/* ================================================== */}

        <section className="min-w-0 flex-1">


          {/* HEADER */}

          <header className="sticky top-0 z-20 flex h-[70px] items-center justify-between border-b border-white/10 bg-[#090a0b]/95 px-5 backdrop-blur md:px-8">

            <div className="flex items-center gap-3">

              <div className="text-white/30">
                ☰
              </div>

              <span className="text-sm text-white/55">
                Research
              </span>

            </div>


            <button
              onClick={newResearch}
              className="text-xs text-white/45 hover:text-white"
            >
              + New research
            </button>

          </header>


          {/* CONTENT */}

          <div className="mx-auto max-w-[930px] px-5 pb-40 pt-12 md:px-10">


            {/* ================================================= */}
            {/* EMPTY */}
            {/* ================================================= */}

            {showEmpty && (

              <div className="flex min-h-[65vh] flex-col items-center justify-center text-center">

                <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-white text-lg font-bold text-black">
                  S
                </div>


                <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">
                  What do you want to research?
                </h1>


                <p className="mt-4 max-w-xl text-sm leading-6 text-white/40">
                  Ask about Indian markets,
                  companies, sectors,
                  financial concepts,
                  or recent market news.
                </p>


                <div className="mt-8 flex flex-wrap justify-center gap-2">

                  {suggestions.map(
                    (suggestion) => (

                      <button
                        key={suggestion}
                        onClick={() =>
                          submitResearch(
                            undefined,
                            suggestion,
                          )
                        }
                        className="rounded-full border border-white/10 px-4 py-2 text-xs text-white/50 hover:border-white/20 hover:text-white"
                      >
                        {suggestion}
                      </button>

                    ),
                  )}

                </div>

              </div>

            )}


            {/* ================================================= */}
            {/* ACTIVE SESSION */}
            {/* ================================================= */}

            {activeSession && (

              <>

                {/* SESSION TITLE */}

                <div className="mb-8">

                  <div className="mb-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-white/30">
                    Research session
                  </div>


                  <h1 className="text-3xl font-semibold leading-tight tracking-tight md:text-4xl">
                    {activeSession.title}
                  </h1>


                  <div className="mt-3 text-xs text-white/25">
                    {activeSession.messages.filter(
                      (message) =>
                        message.role ===
                        "user",
                    ).length}{" "}
                    questions in this research
                  </div>

                </div>


                {/* SAFETY */}

                <div className="mb-8 rounded-xl border border-white/10 bg-white/[0.025] px-4 py-3 text-xs leading-5 text-white/40">

                  SentiNews provides educational
                  and informational market research.
                  It does not provide personalized
                  investment advice, buy/sell
                  recommendations, or price targets.

                </div>


                {/* ================================================= */}
                {/* CHAT */}
                {/* ================================================= */}

                <div className="space-y-10">

                  {activeSession.messages.map(
                    (message) => {

                      if (
                        message.role ===
                        "user"
                      ) {

                        return (

                          <div
                            key={message.id}
                            className="mt-8"
                          >

                            <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/25">
                              You
                            </div>


                            <div className="rounded-2xl border border-white/10 bg-white/[0.035] px-5 py-4 text-sm leading-6 text-white/80">
                              {message.content}
                            </div>

                          </div>

                        );
                      }


                      return (
                        <AssistantMessage
                          key={message.id}
                          message={message}
                        />
                      );

                    },
                  )}

                </div>


                {/* RESEARCHING */}

                {loading && (

                  <div className="mt-8">

                    <div className="flex items-center gap-3">

                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-xs font-bold text-black">
                        S
                      </div>

                      <div>

                        <div className="text-sm font-medium">
                          SentiNews
                        </div>

                        <div className="text-[10px] text-white/25">
                          Researching...
                        </div>

                      </div>

                    </div>


                    <div className="mt-5 rounded-xl border border-white/10 bg-white/[0.02] p-5">

                      <div className="h-3 w-32 animate-pulse rounded bg-white/10" />

                      <div className="mt-5 h-4 w-4/5 animate-pulse rounded bg-white/10" />

                      <div className="mt-3 h-4 w-3/5 animate-pulse rounded bg-white/10" />

                      <div className="mt-3 h-4 w-2/3 animate-pulse rounded bg-white/10" />

                    </div>

                  </div>

                )}


                {/* ERROR */}

                {error && (

                  <div className="mt-6 rounded-xl border border-red-500/20 bg-red-500/5 p-5">

                    <div className="text-sm font-medium text-red-300">
                      Research error
                    </div>

                    <p className="mt-2 text-xs leading-5 text-red-200/60">
                      {error}
                    </p>

                  </div>

                )}

              </>

            )}

          </div>


          {/* ================================================== */}
          {/* ASK BAR */}
          {/* ================================================== */}

          <div className="fixed bottom-0 left-0 right-0 z-30 border-t border-white/10 bg-[#090a0b]/95 px-4 py-4 backdrop-blur lg:left-[260px]">

            <form
              onSubmit={submitResearch}
              className="mx-auto max-w-[800px]"
            >

              <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-[#151719] px-4 py-2">

                <input
                  value={query}
                  onChange={(event) =>
                    setQuery(
                      event.target.value,
                    )
                  }
                  disabled={loading}
                  placeholder={
                    activeSession
                      ? "Ask a follow-up question..."
                      : "Ask SentiNews..."
                  }
                  className="min-w-0 flex-1 bg-transparent py-3 text-sm text-white outline-none placeholder:text-white/25"
                />


                <button
                  type="submit"
                  disabled={
                    loading ||
                    !query.trim()
                  }
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white text-black transition disabled:cursor-not-allowed disabled:opacity-30"
                >
                  ↑
                </button>

              </div>


              <div className="mt-2 text-center text-[9px] text-white/20">
                Research only · Verify important
                financial information with primary
                sources.
              </div>

            </form>

          </div>

        </section>

      </div>

    </main>
  );
}