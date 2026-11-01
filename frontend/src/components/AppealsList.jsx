import { useEffect, useState } from "react";
import AppealDetails from "./AppealDetails";
const statusNames = {
  new: "Новое",
  in_progress: "В работе",
  resolved: "Решено",
  closed: "Закрыто",
};

const priorityNames = {
  low: "Низкий",
  medium: "Средний",
  high: "Высокий",
  critical: "Критический",
};

function AppealsList() {
  // Данные обращений
  const [appeals, setAppeals] = useState([]);
  const [categories, setCategories] = useState([]);

  // Пагинация
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);

  // Фильтры
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [categoryId, setCategoryId] = useState("");

  // Сортировка
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState("desc");

  // Состояния загрузки
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [categoriesError, setCategoriesError] = useState(null);

  // Отдельное состояние для поиска с задержкой
  const [debouncedSearch, setDebouncedSearch] = useState("");

  // Cостояние хранит ID обращения, которое выбрал пользователь
  const [selectedAppealId, setSelectedAppealId] = useState(null);

  // Загрузка категорий
  useEffect(() => {
    const controller = new AbortController();

    async function loadCategories() {
      try {
        const response = await fetch("http://localhost:8000/api/categories", {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP error: ${response.status}`);
        }

        const data = await response.json();

        setCategories(data);
      } catch (err) {
        if (err.name !== "AbortError") {
          setCategoriesError(err.message);
        }
      }
    }

    loadCategories();

    return () => controller.abort();
  }, []);

  // Задержка перед поисковым запросом
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search.trim());
    }, 300);

    return () => clearTimeout(timer);
  }, [search]);

  // Загрузка обращений
  useEffect(() => {
    const controller = new AbortController();

    async function loadAppeals() {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        page: String(page),
        page_size: "10",
        sort_by: sortBy,
        sort_order: sortOrder,
      });

      if (debouncedSearch) {
        params.append("search", debouncedSearch);
      }

      if (status) {
        params.append("status", status);
      }

      if (priority) {
        params.append("priority", priority);
      }

      if (categoryId) {
        params.append("category_id", categoryId);
      }

      try {
        const response = await fetch(
          `http://localhost:8000/api/appeals?${params}`,
          { signal: controller.signal },
        );

        if (!response.ok) {
          throw new Error(`HTTP error: ${response.status}`);
        }

        const data = await response.json();

        setAppeals(data.items);
        setTotalPages(data.total_pages);
        setTotal(data.total);
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

    loadAppeals();

    return () => controller.abort();
  }, [page, debouncedSearch, status, priority, categoryId, sortBy, sortOrder]);

  // Сброс фильтров
  function resetFilters() {
    setSearch("");
    setDebouncedSearch("");
    setStatus("");
    setPriority("");
    setCategoryId("");
    setSortBy("created_at");
    setSortOrder("desc");
    setPage(1);
  }

  return (
    <section className="appeals-section">
      <div className="appeals-heading">
        <h2>Список обращений</h2>
        <span>Найдено: {total}</span>
      </div>

      {/* Панель поиска и фильтрации */}
      <div className="appeals-filters">
        <div className="search-field">
          <input
            type="text"
            placeholder="Поиск по обращениям..."
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
          />
        </div>

        <div className="filters-row">
          {/* Статус */}
          <select
            value={status}
            onChange={(event) => {
              setStatus(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Все статусы</option>

            {Object.entries(statusNames).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>

          {/* Категория */}
          <select
            value={categoryId}
            onChange={(event) => {
              setCategoryId(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Все категории</option>

            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>

          {/* Приоритет */}
          <select
            value={priority}
            onChange={(event) => {
              setPriority(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Все приоритеты</option>

            {Object.entries(priorityNames).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>

          {/* Поле сортировки */}
          <select
            value={sortBy}
            onChange={(event) => {
              setSortBy(event.target.value);
              setPage(1);
            }}
          >
            <option value="created_at">По дате создания</option>
            <option value="updated_at">По дате обновления</option>
            <option value="priority">По приоритету</option>
          </select>

          {/* Направление сортировки */}
          <select
            value={sortOrder}
            onChange={(event) => {
              setSortOrder(event.target.value);
              setPage(1);
            }}
          >
            <option value="desc">По убыванию</option>
            <option value="asc">По возрастанию</option>
          </select>

          <button type="button" className="reset-button" onClick={resetFilters}>
            Сбросить
          </button>
        </div>

        {categoriesError && (
          <p className="error">
            Не удалось загрузить категории: {categoriesError}
          </p>
        )}
      </div>

      {/* Состояния загрузки */}
      {loading && <p>Загрузка обращений...</p>}

      {error && <p className="error">Ошибка загрузки обращений: {error}</p>}

      {!loading && !error && appeals.length === 0 && (
        <p>Обращения не найдены.</p>
      )}
      {/* Подробная информация об обращении */}
      {selectedAppealId !== null && (
        <AppealDetails
          appealId={selectedAppealId}
          onClose={() => setSelectedAppealId(null)}
          statusNames={statusNames}
          priorityNames={priorityNames}
        />
      )}
      {/* Таблица */}
      {!loading && !error && appeals.length > 0 && (
        <>
          <div className="table-wrapper">
            <table className="appeals-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Заголовок</th>
                  <th>Категория</th>
                  <th>Статус</th>
                  <th>Приоритет</th>
                  <th>Дата создания</th>
                </tr>
              </thead>

              <tbody>
                {appeals.map((appeal) => (
                  <tr key={appeal.id}>
                    <td>{appeal.id}</td>

                    <td>
                      <button
                        type="button"
                        className="appeal-title-button"
                        onClick={() => setSelectedAppealId(appeal.id)}
                      >
                        {appeal.title}
                      </button>
                    </td>

                    <td>{appeal.category_name ?? "Без категории"}</td>

                    <td>{statusNames[appeal.status] ?? appeal.status}</td>

                    <td>{priorityNames[appeal.priority] ?? appeal.priority}</td>

                    <td>
                      {new Date(appeal.created_at).toLocaleString("ru-RU")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Пагинация */}
          <div className="pagination">
            <button disabled={page === 1} onClick={() => setPage(page - 1)}>
              Назад
            </button>

            <span>
              Страница {page} из {totalPages}
            </span>

            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
            >
              Далее
            </button>
          </div>
        </>
      )}
    </section>
  );
}

export default AppealsList;
