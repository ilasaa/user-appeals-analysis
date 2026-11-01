import { useEffect, useState } from "react";
import AppealsList from "./components/AppealsList";

function App() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadSummary() {
      try {
        const response = await fetch(
          "http://localhost:8000/api/analytics/summary",
          { signal: controller.signal },
        );

        if (!response.ok) {
          throw new Error(`HTTP error: ${response.status}`);
        }

        const data = await response.json();

        setSummary(data);
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadSummary();

    return () => controller.abort();
  }, []);

  return (
    <main className="dashboard">
      <header>
        <h1>Анализ обращений пользователей</h1>
        <p>Панель управления</p>
      </header>

      {loading && <p>Загрузка статистики...</p>}

      {error && <p className="error">Ошибка: {error}</p>}

      {summary && (
        <section className="stats">
          <div className="card">
            <h3>Всего обращений</h3>
            <p>{summary.total_appeals}</p>
          </div>

          <div className="card">
            <h3>Новые</h3>
            <p>{summary.new_appeals}</p>
          </div>

          <div className="card">
            <h3>В работе</h3>
            <p>{summary.in_progress_appeals}</p>
          </div>

          <div className="card">
            <h3>Решённые</h3>
            <p>{summary.resolved_appeals}</p>
          </div>

          <div className="card">
            <h3>Закрытые</h3>
            <p>{summary.closed_appeals}</p>
          </div>
        </section>
      )}
      <AppealsList />
    </main>
  );
}

export default App;
