import { useState, useCallback } from "react";
import { searchUsers, type UserResult } from "../api";
import ChartCard from "./ChartCard";
import "./UserSearch.css";

export default function UserSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<UserResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = useCallback(async () => {
    const trimmed = query.trim();
    if (trimmed.length < 2) return;
    setLoading(true);
    setError(null);
    try {
      const res = await searchUsers(trimmed);
      setResults(res.data ?? []);
      setSearched(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Search failed");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [query]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSearch();
  };

  return (
    <ChartCard title="Search Users" className="user-search">
      <div style={{ width: "100" }}>
        {/* Search bar */}
        <div className="user-search-bar">
          <input
            type="text"
            placeholder="Search by phone number, name, or email…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button onClick={handleSearch} disabled={loading || query.trim().length < 2}>
            {loading ? "Searching…" : "Search"}
          </button>
        </div>
        <p className="user-search-hint">
          Enter at least 2 characters to search by phone, name, or email
        </p>

        {/* Error */}
        {error && <p style={{ color: "#ef4444", fontSize: "0.85rem" }}>{error}</p>}

        {/* Results */}
        {searched && !error && (
          results.length === 0 ? (
            <p className="user-no-results">No users found matching "{query.trim()}"</p>
          ) : (
            <div className="user-results-scroll">
              <table className="user-results-table">
                <thead>
                  <tr>
                    <th>Phone</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Region / City</th>
                    <th>UTM Source</th>
                    <th>UTM Campaign</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((u) => (
                    <tr key={u._id}>
                      <td>{u.phone}</td>
                      <td>
                        <div className="cell-list">
                          {u.name?.map((n, i) => (
                            <span key={i} className="user-tag">{n}</span>
                          ))}
                        </div>
                      </td>
                      <td>
                        <div className="cell-list">
                          {u.email?.map((e, i) => (
                            <span key={i} className="user-tag">{e}</span>
                          ))}
                        </div>
                      </td>
                      <td>
                        <div className="cell-list">
                          {u.geo_region?.map((r, i) => (
                            <span key={i} className="user-tag region">{r}</span>
                          ))}
                          {u.geo_city?.map((c, i) => (
                            <span key={`c${i}`} className="user-tag">{c}</span>
                          ))}
                        </div>
                      </td>
                      <td>
                        <div className="cell-list">
                          {u.utm_source?.map((s, i) => (
                            <span key={i} className="user-tag source">{s}</span>
                          ))}
                        </div>
                      </td>
                      <td>
                        <div className="cell-list">
                          {u.utm_campaign?.map((c, i) => (
                            <span key={i} className="user-tag campaign">{c}</span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        )}
      </div>
    </ChartCard>
  );
}
