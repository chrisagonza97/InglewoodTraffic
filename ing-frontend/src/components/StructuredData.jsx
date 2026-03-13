export default function StructuredData({ events }) {
    if (!events || events.length === 0) return null;
  
    const structuredData = {
      "@context": "https://schema.org",
      "@type": "ItemList",
      "name": "Inglewood Events",
      "description": "Upcoming events at SoFi Stadium, Kia Forum, and Intuit Dome",
      "itemListElement": events.slice(0, 20).map((event, index) => ({
        "@type": "ListItem",
        "position": index + 1,
        "item": {
          "@type": "Event",
          "name": event.title,
          "location": {
            "@type": "Place",
            "name": event.venue,
            "address": {
              "@type": "PostalAddress",
              "addressLocality": "Inglewood",
              "addressRegion": "CA",
              "addressCountry": "US"
            }
          },
          "startDate": event.start_at_la,
          "url": event.url,
          "eventStatus": "https://schema.org/EventScheduled"
        }
      }))
    };
  
    return (
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
    );
  }