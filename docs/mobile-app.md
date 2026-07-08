# RouteHub Mobile — design doc

Нативное Android-приложение (Kotlin, Jetpack Compose) поверх существующего FastAPI-бэкенда.
iOS — вне скоупа MVP (при необходимости позже: Kotlin Multiplatform, слой `data/` переносится почти как есть).

## Почему нативный Kotlin

- Карта — центральный UX; нативный `osmdroid`/Google Maps даёт лучшую производительность и жесты, чем WebView/гибриды.
- Геолокация, фоновые чек-ины и push-уведомления (пост-MVP) требуют нативных API.
- Бэкенд уже отдаёт чистый JSON + JWT — клиенту не нужен SSR или общий код с Vue.

## Стек

| Слой         | Выбор                                             | Почему                                             |
|--------------|---------------------------------------------------|----------------------------------------------------|
| UI           | Jetpack Compose + Material 3                      | Стандарт, быстрые итерации                         |
| Навигация    | Navigation Compose (bottom bar + stack)           | Единый граф, deep-link-ready                       |
| Сеть         | Retrofit 2 + OkHttp + Gson                        | Без compiler-плагинов — надёжная сборка на AGP 9   |
| Хранение     | DataStore Preferences (JWT-токен)                 | Замена SharedPreferences, async API                |
| Карта        | osmdroid (OpenStreetMap)                          | Без API-ключа; Mapbox/Google — опционально позже   |
| Архитектура  | Compose state (`remember`/`LaunchedEffect`) + `Session`(StateFlow) | Для MVP без ViewModel/DI; граф зависимостей — в `RouteHubApp` |
| Сборка       | AGP 9.1 (built-in Kotlin 2.2), Gradle 9.6, JDK 17+| Совместимо с JDK 25 на dev-машине                  |

`minSdk 26` (Android 8.0, ~97% устройств), `compileSdk/targetSdk 36`.

## Структура модуля `app`

```text
com.pritilab.routehub/
  RouteHubApp.kt          # Application: ServiceLocator (api, tokenStore, repos)
  data/
    ApiClient.kt          # Retrofit + OkHttp (Authorization interceptor)
    RouteHubApi.kt        # интерфейс всех эндпоинтов /api/v1
    Dto.kt                # data-классы ответов/запросов (Gson)
    TokenStore.kt         # DataStore: JWT access token
    Repos.kt              # AuthRepository, PoiRepository, RouteRepository, SocialRepository
  ui/
    theme/                # Material 3 цвета/типографика
    AppNav.kt             # NavHost + bottom bar (Home, Search, Map, Feed, Profile)
    screens/
      LoginScreen.kt      # вход + регистрация, redirect back
      HomeScreen.kt       # публичные маршруты
      SearchScreen.kt     # гибридный поиск (debounce 350 мс)
      MapScreen.kt        # osmdroid: POI-маркеры, сбор маршрута тапами, создание
      PoiDetailScreen.kt  # рейтинг, отзывы, чек-ин, похожие места
      FeedScreen.kt       # лента подписок (чек-ины/отзывы/маршруты)
      ProfileScreen.kt    # профиль, follow/unfollow, счётчики
```

## Контракт с бэкендом

Используются существующие эндпоинты `/api/v1/*` без изменений: `auth/{register,login,me}`,
`pois` (список bbox/geo, деталь, `checkin`, `reviews`, `similar`), `search/pois/hybrid`,
`routes` (list/create/save), `feed`, `users/{username}` (+follow/followers/following).

- Координаты в JSON — `{lat, lng}` (Pydantic-сторона), как в вебе.
- Auth: `Authorization: Bearer <access_token>`; токен в DataStore, подставляется OkHttp-интерцептором.
- База API задаётся в `local.properties` → `BuildConfig.API_BASE_URL`;
  по умолчанию `http://10.0.2.2:8010/api/v1` (эмулятор → хостовый Docker, порт из `.env`).
  Для dev разрешён cleartext-HTTP только на debug-сборке (network security config).

## Состояния и ошибки

- Каждый экран: `UiState { loading | data | error(message, retry) }` через `StateFlow` во ViewModel.
- 401 → сброс токена + переход на Login (как `fetchMe()` в вебе).
- Сеть недоступна → карточка с Retry; карта работает офлайн на кэше тайлов osmdroid.

## MVP-скоуп (этот коммит)

Login/Register, Home (маршруты), гибридный Search, Map с POI и созданием маршрута
(выбор точек тапом, авто-оптимизация на сервере), POI Detail (отзыв, чек-ин, похожие),
Feed, Profile (follow/unfollow). Всё read/write через существующий API.

## Пост-MVP

Создание POI с карты, сохранённые маршруты офлайн, push (FCM) на активность подписок,
фото POI, переход на Mapbox SDK, KMP-ядро для iOS.
