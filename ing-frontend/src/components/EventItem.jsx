import { formatLATime } from "../utils/time";

export default function EventItem({ ev }) {
  const start = ev.start_at_la ? formatLATime(ev.start_at_la) : "TBA";
  return (
    <li className="event">
      <div className="event-title">{ev.title}</div>
      <div className="event-meta">
        <span>{ev.venue}</span>
        <span>•</span>
        <span>{start}</span>
        <span>•</span>
        <a href={ev.url} target="_blank" rel="noreferrer">Details</a>
      </div>
    </li>
  );
}
