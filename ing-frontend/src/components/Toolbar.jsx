export default function Toolbar({ onRefresh, isFetching }) {
    return (
      <div className="toolbar">
        <button onClick={onRefresh} disabled={isFetching}>
          {isFetching ? "Refreshing…" : "Refresh"}
        </button>
      </div>
    );
  }
  