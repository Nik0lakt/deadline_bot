from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

DATE_PATTERNS = [
    re.compile(r"^(?P<d>\d{2})\.(?P<m>\d{2})$"),               # DD.MM
    re.compile(r"^(?P<d>\d{2})\.(?P<m>\d{2})\.(?P<y>\d{4})$"), # DD.MM.YYYY
    re.compile(r"^(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})$"),   # YYYY-MM-DD
]

@dataclass
class TaskCommand:
    title: str
    deadline: date
    assignee_username: str  # без '@'

class ParseError(Exception):
    pass

def _parse_date(value: str) -> date:
    value = value.strip()
    today = date.today()

    for p in DATE_PATTERNS:
        m = p.match(value)
        if not m:
            continue
        gd = m.groupdict()
        y = int(gd.get("y") or today.year)
        mth = int(gd["m"])
        d = int(gd["d"])
        return date(y, mth, d)
    raise ParseError("Не удалось распознать дату. Поддерживаемые форматы: DD.MM, DD.MM.YYYY, YYYY-MM-DD.")

def parse_task_command(text: str) -> TaskCommand:
    """
    Алгоритм:
      1) убрать '/task' в начале
      2) найти ключевое слово 'до' (как отдельное слово)
      3) слева -> title, справа -> первое слово дата, второе слово (если начинается с @) -> username
    """
    if not text:
        raise ParseError("Пустая команда.")

    # Убираем команду с возможными параметрами бота (/task@bot)
    text = text.strip()
    text = re.sub(r"^/task(@[A-Za-z0-9_]+)?\s*", "", text, flags=re.IGNORECASE)

    # Ищем 'до' как отдельное слово
    m = re.search(r"\bдо\b", text, flags=re.IGNORECASE)
    if not m:
        raise ParseError("Не найдено ключевое слово 'до'.")

    left = text[:m.start()].strip()
    right = text[m.end():].strip()
    if not left:
        raise ParseError("Не указан заголовок задачи перед 'до'.")

    parts = right.split()
    if len(parts) == 0:
        raise ParseError("После 'до' должна быть дата.")
    date_str = parts[0]
    assignee_username = ""
    if len(parts) >= 2 and parts[1].startswith("@"):
        assignee_username = parts[1][1:]  # без @

    if not assignee_username:
        raise ParseError("Не указан исполнитель (@username).")

    deadline = _parse_date(date_str)
    return TaskCommand(title=left, deadline=deadline, assignee_username=assignee_username)
