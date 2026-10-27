# Общая часть запроса для получения обращений
APPEALS_SELECT = """
    SELECT
        a.id,
        a.title,
        a.description,
        a.category_id,
        c.name AS category_name,
        a.status,
        a.priority,
        a.created_at,
        a.updated_at,
        a.resolved_at
    FROM appeals AS a
    LEFT JOIN categories AS c
        ON a.category_id = c.id
"""


# Получить обращения с фильтрацией
# Общие условия фильтрации обращений
APPEALS_FILTERS = """
    WHERE
        (
            %(status)s::text IS NULL
            OR a.status = %(status)s::text
        )
        AND (
            %(priority)s::text IS NULL
            OR a.priority = %(priority)s::text
        )
        AND (
            %(category_id)s::bigint IS NULL
            OR a.category_id = %(category_id)s::bigint
        )
        AND (
            %(search)s::text IS NULL
            OR a.title ILIKE %(search)s::text
            OR a.description ILIKE %(search)s::text
        )
"""


# Получить обращения с фильтрацией
GET_APPEALS = APPEALS_SELECT + APPEALS_FILTERS


# Получить количество обращений с учётом фильтров
COUNT_APPEALS = """
    SELECT COUNT(*) AS total
    FROM appeals AS a
""" + APPEALS_FILTERS


# Получить обращение по ID
GET_APPEAL_BY_ID = APPEALS_SELECT + """
    WHERE a.id = %s;
"""


# Проверить существование категории
GET_CATEGORY_BY_ID = """
    SELECT
        id,
        name,
        description,
        created_at
    FROM categories
    WHERE id = %s;
"""


# Создать обращение
CREATE_APPEAL = """
    INSERT INTO appeals (
        title,
        description,
        category_id,
        priority
    )
    VALUES (%s, %s, %s, %s)
    RETURNING id;
"""

# Получить все категории
GET_CATEGORIES = """
    SELECT
        id,
        name,
        description,
        created_at
    FROM categories
    ORDER BY name;
"""


# Создать категорию
CREATE_CATEGORY = """
    INSERT INTO categories (
        name,
        description
    )
    VALUES (%s, %s)
    ON CONFLICT (name) DO NOTHING
    RETURNING id;
"""

# Изменить статус обращения
UPDATE_APPEAL_STATUS = """
    UPDATE appeals
    SET
        status = %(status)s::text,
        updated_at = CURRENT_TIMESTAMP,
        resolved_at = CASE
            WHEN %(status)s::text = 'resolved'
                THEN COALESCE(resolved_at, CURRENT_TIMESTAMP)
            WHEN %(status)s::text IN ('new', 'in_progress')
                THEN NULL
            ELSE resolved_at
        END
    WHERE id = %(appeal_id)s
    RETURNING id;
"""

# Редактировать обращение
UPDATE_APPEAL = """
    UPDATE appeals
    SET
        title = CASE
            WHEN %(change_title)s::boolean
                THEN %(title)s::text
            ELSE title
        END,

        description = CASE
            WHEN %(change_description)s::boolean
                THEN %(description)s::text
            ELSE description
        END,

        category_id = CASE
            WHEN %(change_category)s::boolean
                THEN %(category_id)s::bigint
            ELSE category_id
        END,

        priority = CASE
            WHEN %(change_priority)s::boolean
                THEN %(priority)s::text
            ELSE priority
        END,

        updated_at = CURRENT_TIMESTAMP

    WHERE id = %(appeal_id)s
    RETURNING id;
"""
# Удалить обращение
DELETE_APPEAL = """
    DELETE FROM appeals
    WHERE id = %s
    RETURNING id;
"""

# Получить общую статистику обращений
GET_ANALYTICS_SUMMARY = """
    SELECT
        COUNT(*) AS total_appeals,

        COUNT(*) FILTER (
            WHERE status = 'new'
        ) AS new_appeals,

        COUNT(*) FILTER (
            WHERE status = 'in_progress'
        ) AS in_progress_appeals,

        COUNT(*) FILTER (
            WHERE status = 'resolved'
        ) AS resolved_appeals,

        COUNT(*) FILTER (
            WHERE status = 'closed'
        ) AS closed_appeals,

        ROUND(
            AVG(
                EXTRACT(
                    EPOCH FROM (resolved_at - created_at)
                ) / 3600
            ) FILTER (
                WHERE status IN ('resolved', 'closed')
                    AND resolved_at IS NOT NULL
            ),
            2
        ) AS average_resolution_hours

    FROM appeals;
"""

# Статистика обращений по категориям
GET_ANALYTICS_CATEGORIES = """
    SELECT
        c.id AS category_id,
        c.name AS category_name,
        COUNT(a.id) AS appeals_count

    FROM categories AS c

    LEFT JOIN appeals AS a
        ON a.category_id = c.id

    GROUP BY c.id, c.name

    UNION ALL

    SELECT
        NULL AS category_id,
        'Без категории' AS category_name,
        COUNT(*) AS appeals_count

    FROM appeals
    WHERE category_id IS NULL

    HAVING COUNT(*) > 0

    ORDER BY appeals_count DESC, category_name ASC;
"""