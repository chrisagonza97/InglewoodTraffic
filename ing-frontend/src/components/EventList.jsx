import EventItem from "./EventItem";

export default function EventList({ items }) {
  if (!items || items.length === 0) {
    return <div className="empty">No events.</div>;
  }
  return (
    <ul className="event-list">
      {items.map((ev, i) => (
        <EventItem key={`${ev.venue}-${ev.title}-${i}`} ev={ev} />
      ))}
    </ul>
  );
}
