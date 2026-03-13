import { QueryClient, QueryClientProvider, useQueryClient } from "@tanstack/react-query";
import { useTodayEvents, useUpcomingEvents, useWeekEvents } from "./hooks/useEvents";
import Section from "./components/Section";
import EventList from "./components/EventList";
import Toolbar from "./components/Toolbar";
import Tabs from "./components/Tabs";
import Alert from "./components/Alert";
import { oneHourBeforeISO, formatLATime } from "./utils/time";
import "./index.css";
import { useState, useMemo } from "react";
import MapPanel from "./components/MapPanel";
import { CUSTOM_CORRIDORS, directionsUrl } from "./maps/corridors";
import StructuredData from "./components/StructuredData";


const qc = new QueryClient();

function Page() {
  const queryClient = useQueryClient();
  const [weekTab, setWeekTab] = useState(0);

  const { data: today = [], isLoading: l1, isFetching: f1, error: e1 } = useTodayEvents();
  const { data: upcoming = [], isLoading: l2, isFetching: f2, error: e2 } = useUpcomingEvents(100);
  const { data: weekData = [], isLoading: lW, isFetching: fW, error: eW } = useWeekEvents(weekTab, 300);

  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["events", "today"] }),
      queryClient.invalidateQueries({ queryKey: ["events", "upcoming"] }),
      queryClient.invalidateQueries({ queryKey: ["events", "week"] }),
    ]);
  };

  // --- Advisory for today's earliest event ---
  const advisory = useMemo(() => {
    if (!today.length) return null;
    // choose the earliest start_at_la that exists
    const withStart = today.filter(ev => ev.start_at_la);
    if (!withStart.length) return null;
    withStart.sort((a, b) => new Date(a.start_at_la) - new Date(b.start_at_la));
    const first = withStart[0];
    const advisoryISO = oneHourBeforeISO(first.start_at_la); // UTC instant minus 60 min
    const advisoryTextLA = formatLATime(advisoryISO);        // show LA wall-clock
    const eventTimeLA = formatLATime(first.start_at_la);
    return {
      venue: first.venue,
      title: first.title,
      advisoryTextLA,
      eventTimeLA,
    };
  }, [today]);

  return (
    <main className="container">
      <header className="header">
        <div className="header-content">
          <h1>Inglewood Events</h1>
          <p className="intro">
            Live updates for SoFi Stadium, Kia Forum, and Intuit Dome
          </p>
        </div>
        <Toolbar onRefresh={refresh} isFetching={f1 || f2 || fW} />
      </header>

      {/* TODAY first */}
      <Section title="Today" count={today.length}>
        {advisory && (
          <Alert>
            Expect increased traffic around <strong>{advisory.advisoryTextLA}</strong> near <strong>{advisory.venue}</strong> for <em>{advisory.title}</em> (starts {advisory.eventTimeLA}).
          </Alert>
        )}
        {l1 ? (
          <div className="skeleton">Loading…</div>
        ) : e1 ? (
          <div className="error">{String(e1.message || e1)}</div>
        ) : (
          <EventList items={today} />
        )}
      </Section>

      {/*Map Traffic */}
      <section className="section">
        <div className="section-header">
          <h2>Traffic Map - Century Blvd & Prairie Ave</h2>
        </div>

        {Object.entries(CUSTOM_CORRIDORS).map(([id, c]) => {
          const center = c.polyline[Math.floor(c.polyline.length / 2)];
          const mapsLink = directionsUrl(c.origin, c.destination);
          return (
            <div key={id} style={{ marginBottom: 16 }}>
              <div className="toolbar" style={{ marginBottom: 8, display: "flex", gap: 8, alignItems: "center" }}>
                <strong>{c.label}</strong>
                <a href={mapsLink} target="_blank" rel="noreferrer" className="btn">
                  Open in Google Maps (live traffic)
                </a>
              </div>
              <MapPanel
                polyline={c.polyline}
                center={center}
                originLabel="Start"
                destLabel="End (~1 mile)"
              />
            </div>
          );
        })}
      </section>

      {/* THIS/NEXT WEEK */}
      <Section title="This Week / Next Week" count={weekData.length}>
        <Tabs
          value={weekTab}
          onChange={setWeekTab}
          tabs={[
            { value: 0, label: "This Week" },
            { value: 1, label: "Next Week" },
          ]}
        />
        {lW ? (
          <div className="skeleton">Loading…</div>
        ) : eW ? (
          <div className="error">{String(eW.message || eW)}</div>
        ) : (
          <EventList items={weekData} />
        )}
      </Section>

      {/* UPCOMING */}
      <Section title="Upcoming" count={upcoming.length}>
        {l2 ? <div className="skeleton">Loading…</div> : e2 ? <div className="error">{String(e2.message || e2)}</div> : <EventList items={upcoming} />}
      </Section>

      <footer className="footer">
        <small>
          Inglewood Events - SoFi Stadium, Kia Forum, Intuit Dome • 
          Live traffic alerts for Century Blvd & Prairie Ave • 
          Times shown in America/Los_Angeles • 
          Data cached client-side
        </small>
      </footer>
    </main>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <Page />
    </QueryClientProvider>
  );
}
