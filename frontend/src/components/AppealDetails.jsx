import { useEffect, useState } from "react";

function AppealDetails({
  appealId,
  onClose,
  statusNames,
  priorityNames,
}) {
  const [appeal, setAppeal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadAppeal() {
      setLoading(true);
      setError(null);
      setAppeal(null);

      try {
        const response = await fetch(
          `http://localhost:8000/api/appeals/${appealId}`,
          { signal: controller.signal }
        );

        if (!response.ok) {
          throw new Error(`HTTP error: ${response.status}`);
        }

        const data = await response.json();

        setAppeal(data);
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

    loadAppeal();

    return () => controller.abort();
  }, [appealId]);

  function formatDate(date) {
    if (!date) {
      return "—";
    }

    return new Date(date).toLocaleString("ru-RU");
  }

  return (
    <section className="appeal-details">

      <div className="appeal-details-header">
        <h2>Подробная информация</h2>

        <button
          type="button"
          className="close-details-button"
          onClick={onClose}
        >
          Закрыть
        </button>
      </div>

      {loading && <p>Загрузка обращения...</p>}

      {error && (
        <p className="error" role="alert">
          Ошибка загрузки: {error}
        </p>
      )}

      {!loading && !error && appeal && (
        <>
          <h3>
            #{appeal.id} — {appeal.title}
          </h3>

          <div className="appeal-description">
            <h4>Описание проблемы</h4>
            <p>{appeal.description}</p>
          </div>

          <div className="appeal-info-grid">

            <div>
              <span>Категория</span>
              <strong>
                {appeal.category_name ?? "Без категории"}
              </strong>
            </div>

            <div>
              <span>Статус</span>
              <strong>
                {statusNames[appeal.status] ?? appeal.status}
              </strong>
            </div>

            <div>
              <span>Приоритет</span>
              <strong>
                {priorityNames[appeal.priority] ?? appeal.priority}
              </strong>
            </div>

            <div>
              <span>Дата создания</span>
              <strong>
                {formatDate(appeal.created_at)}
              </strong>
            </div>

            <div>
              <span>Последнее изменение</span>
              <strong>
                {formatDate(appeal.updated_at)}
              </strong>
            </div>

            <div>
              <span>Дата решения</span>
              <strong>
                {formatDate(appeal.resolved_at)}
              </strong>
            </div>

          </div>
        </>
      )}
    </section>
  );
}

export default AppealDetails;