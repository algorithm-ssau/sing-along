# sing-along

## Запуск проекта

**Запуск возможен только под linux**

1. Установить [uv](https://github.com/astral-sh/uv)
2. Создать окружение uv

```shell
uv sync
```

3. Если есть видеокарта AMD - настройте поддержку [ROCm](https://rocm.docs.amd.com/en/latest/). Поддержка видеокарт Nvidia пока не предусмотрена
4. Задайте переменные окружения

| Название     | Описание            |
|--------------|---------------------|
| GENIUS_TOKEN | Ключ апи genius.com |
| BOT_API_KEY  | Ключ бота телеграм  |

5. Запустите бота
```shell
uv run telegram-bot/bot.py
```
