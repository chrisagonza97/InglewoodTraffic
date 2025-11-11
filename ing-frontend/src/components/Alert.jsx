export default function Alert({ children }) {
    if (!children) return null;
    return (
      <div className="alert">
        {children}
      </div>
    );
  }
  