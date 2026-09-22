"use client";

// Sample flow for services/sample-api. The client-builder agent replaces this page with the
// design's acceptance flows (design/spec.md), keeping the same pattern: typed calls via lib/api.

import { useCallback, useEffect, useState } from "react";
import type { components } from "@/api/sample-api";
import { api } from "@/lib/api";

type Item = components["schemas"]["Item"];
type Source = "primary" | "replica";

export default function Home() {
  const [items, setItems] = useState<Item[]>([]);
  const [name, setName] = useState("");
  const [source, setSource] = useState<Source>("primary");
  const [servedBy, setServedBy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await api<Item[]>("sample-api", `/items?source=${source}`);
      setItems(res.data);
      setServedBy(res.servedBy);
      setError(null);
    } catch (e) {
      setError(String(e));
    }
  }, [source]);

  useEffect(() => {
    load();
  }, [load]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      await api<Item>("sample-api", "/items", { method: "POST", body: JSON.stringify({ name }) });
      setName("");
      await load();
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <>
      <h1>Sample: items</h1>
      <p className="muted">
        Writes go to the Postgres primary. Read from a replica right after writing to see replication lag.
      </p>
      <form onSubmit={add}>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="New item" aria-label="Item name" />
        <button type="submit">Add</button>
        <select value={source} onChange={(e) => setSource(e.target.value as Source)} aria-label="Read from">
          <option value="primary">read: primary</option>
          <option value="replica">read: replica</option>
        </select>
      </form>
      {error && <p className="error">{error}</p>}
      <p className="muted">
        served by <code>{servedBy ?? "—"}</code>
      </p>
      <table>
        <thead>
          <tr>
            <th>id</th>
            <th>name</th>
            <th>created</th>
          </tr>
        </thead>
        <tbody>
          {items.map((i) => (
            <tr key={i.id}>
              <td>{i.id}</td>
              <td>{i.name}</td>
              <td className="muted">{new Date(i.created_at).toLocaleTimeString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
