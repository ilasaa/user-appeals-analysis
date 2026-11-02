import { useEffect, useState } from "react";

import AppealDetails from "./AppealDetails";
import CreateAppeal from "./CreateAppeal";


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


function AppealsList({ onAppealsChanged }) {
  // Данные
  const [appeals, setAppeals] = useState([]);
  const [categories, setCategories] = useState([]);

  // Пагинация
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);

  // Фильтрация
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

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

  // Подробная информация
  const [selectedAppealId, setSelectedAppealId] = useState(null);

  // Создание обращений
  const [showCreateForm, setShowCreateForm] = useState(false);

  // Повторная загрузка списка
  const [reloadKey, setReloadKey] = useState(0);


  // Загрузка категорий
  useEffect(() => {
    const controller = new AbortController();

    async function loadCategories() {
      try {
        const response = await fetch(
          "http://localhost:8000/api/categories",
          { signal: controller.signal }
        );

        if (!response.ok) {
          throw new Error(`HTTP error: ${response.status}`);
        }

        const data = await response.json();

        setCategories(data);
        setCategoriesError(null);
      } catch (err) {
        if (err.name !== "AbortError") {
          setCategoriesError(err.message);
        }
      }
    }

    loadCategories();

    return () => controller.abort();
  }, []);


  // Задержка поиска
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
          { signal: controller.signal }
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
  }, [
    page,
    debouncedSearch,
    status,
    priority,
    categoryId,
    sortBy,
    sortOrder,
    reloadKey,
  ]);


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


  // Обработка создания нового обращения
  function handleAppealCreated(newAppeal) {
    // Закрываем форму
    setShowCreateForm(false);

    // Сбрасываем фильтры
    resetFilters();

    // Открываем подробную карточку
    setSelectedAppealId(newAppeal.id);

    // Обновляем таблицу
    setReloadKey((value) => value + 1);

    // Обновляем статистику
    onAppealsChanged?.();
  }


  return (
    <section className="appeals-section">

      {/* Заголовок и кнопка создания */}
      <div className="appeals-heading">
        <h2>Список обращений</h2>

        <div className="appeals-heading-actions">
          <span>Найдено: {total}</span>

          {!showCreateForm && (
            <button
              type="button"
              className="primary-button"
              onClick={() => setShowCreateForm(true)}
            >
              + Создать обращение
            </button>
          )}
        </div>
      </div>


      {/* Форма создания обращения */}
      {showCreateForm && (
        <CreateAppeal
          categories={categories}
          onCreated={handleAppealCreated}
          onCancel={() => setShowCreateForm(false)}
        />
      )}


      {/* Поиск и фильтрация */}
      <div className="appeals-filters">

        <div className="search-field">
          <input
            type="text"
            placeholder="Поиск по обращениям..."
            aria-label="Поиск по обращениям"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
          />
        </div>

        <div className="filters-row">

          {/* Фильтр по статусу */}
          <select
            aria-label="Статус обращения"
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


          {/* Фильтр по категории */}
          <select
            aria-label="Категория обращения"
            value={categoryId}
            onChange={(event) => {
              setCategoryId(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Все категории</option>

            {categories.map((category) => (
              <option
                key={category.id}
                value={category.id}
              >
                {category.name}
              </option>
            ))}
          </select>


          {/* Фильтр по приоритету */}
          <select
            aria-label="Приоритет обращения"
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
            aria-label="Поле сортировки"
            value={sortBy}
            onChange={(event) => {
              setSortBy(event.target.value);
              setPage(1);
            }}
          >
            <option value="created_at">
              По дате создания
            </option>

            <option value="updated_at">
              По дате обновления
            </option>

            <option value="priority">
              По приоритету
            </option>
          </select>


          {/* Порядок сортировки */}
          <select
            aria-label="Направление сортировки"
            value={sortOrder}
            onChange={(event) => {
              setSortOrder(event.target.value);
              setPage(1);
            }}
          >
            <option value="desc">
              По убыванию
            </option>

            <option value="asc">
              По возрастанию
            </option>
          </select>


          {/* Сброс */}
          <button
            type="button"
            className="reset-button"
            onClick={resetFilters}
          >
            Сбросить
          </button>

        </div>

        {categoriesError && (
          <p className="error" role="alert">
            Ошибка загрузки категорий: {categoriesError}
          </p>
        )}
      </div>


      {/* Подробная информация об обращении */}
      {selectedAppealId !== null && (
        <AppealDetails
          appealId={selectedAppealId}
          onClose={() => setSelectedAppealId(null)}
          statusNames={statusNames}
          priorityNames={priorityNames}
        />
      )}


      {/* Состояние загрузки */}
      {loading && (
        <p>Загрузка обращений...</p>
      )}

      {error && (
        <p className="error" role="alert">
          Ошибка загрузки обращений: {error}
        </p>
      )}


      {/* Пустой список */}
      {!loading && !error && appeals.length === 0 && (
        <p>Обращения не найдены.</p>
      )}


      {/* Таблица обращений */}
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
                        onClick={() =>
                          setSelectedAppealId(appeal.id)
                        }
                      >
                        {appeal.title}
                      </button>
                    </td>

                    <td>
                      {appeal.category_name ?? "Без категории"}
                    </td>

                    <td>
                      {statusNames[appeal.status] ?? appeal.status}
                    </td>

                    <td>
                      {priorityNames[appeal.priority] ?? appeal.priority}
                    </td>

                    <td>
                      {new Date(
                        appeal.created_at
                      ).toLocaleString("ru-RU")}
                    </td>

                  </tr>
                ))}
              </tbody>
            </table>

          </div>


          {/* Пагинация */}
          <div className="pagination">

            <button
              type="button"
              disabled={page === 1}
              onClick={() => setPage((value) => value - 1)}
            >
              Назад
            </button>

            <span>
              Страница {page} из {totalPages}
            </span>

            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => setPage((value) => value + 1)}
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