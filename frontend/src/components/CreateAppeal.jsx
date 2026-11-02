import { useState } from "react";

function CreateAppeal({ categories, onCreated, onCancel }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [priority, setPriority] = useState("medium");

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(event) {
    event.preventDefault();

    if (saving) {
      return;
    }

    const cleanTitle = title.trim();
    const cleanDescription = description.trim();

    if (cleanTitle.length < 3 || !cleanDescription) {
      setError(
        "Введите заголовок от 3 символов и описание обращения."
      );
      return;
    }

    setSaving(true);
    setError(null);

    const payload = {
      title: cleanTitle,
      description: cleanDescription,
      category_id: categoryId ? Number(categoryId) : null,
      priority: priority,
    };

    try {
      const response = await fetch(
        "http://localhost:8000/api/appeals",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        const message =
          typeof data.detail === "string"
            ? data.detail
            : `Ошибка создания обращения: HTTP ${response.status}`;

        throw new Error(message);
      }

      onCreated(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form
      className="create-appeal-form"
      onSubmit={handleSubmit}
    >
      <h3>Новое обращение</h3>

      <label htmlFor="appeal-title">
        Заголовок

        <input
          id="appeal-title"
          type="text"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          minLength={3}
          maxLength={200}
          required
          placeholder="Введите заголовок обращения"
          disabled={saving}
        />
      </label>

      <label htmlFor="appeal-description">
        Описание проблемы

        <textarea
          id="appeal-description"
          value={description}
          onChange={(event) =>
            setDescription(event.target.value)
          }
          rows={5}
          required
          placeholder="Подробно опишите проблему"
          disabled={saving}
        />
      </label>

      <div className="create-appeal-grid">
        <label htmlFor="appeal-category">
          Категория

          <select
            id="appeal-category"
            value={categoryId}
            onChange={(event) =>
              setCategoryId(event.target.value)
            }
            disabled={saving}
          >
            <option value="">Без категории</option>

            {categories.map((category) => (
              <option
                key={category.id}
                value={category.id}
              >
                {category.name}
              </option>
            ))}
          </select>
        </label>

        <label htmlFor="appeal-priority">
          Приоритет

          <select
            id="appeal-priority"
            value={priority}
            onChange={(event) =>
              setPriority(event.target.value)
            }
            disabled={saving}
          >
            <option value="low">Низкий</option>
            <option value="medium">Средний</option>
            <option value="high">Высокий</option>
            <option value="critical">Критический</option>
          </select>
        </label>
      </div>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      <div className="create-appeal-actions">
        <button
          type="button"
          className="cancel-button"
          onClick={onCancel}
          disabled={saving}
        >
          Отмена
        </button>

        <button
          type="submit"
          className="primary-button"
          disabled={saving}
        >
          {saving ? "Сохранение..." : "Создать обращение"}
        </button>
      </div>
    </form>
  );
}

export default CreateAppeal;