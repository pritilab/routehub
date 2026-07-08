# RouteHub — Рекомендации для фаундера (§24 AufenthG, Bad Oeynhausen)

Версия: 1.0 (июль 2026). Персональный документ: юридический статус,
финансирование и порядок действий для соло-фаундера-разработчика с ВНЖ по
§24 AufenthG (временная защита), проживающего в Бад-Ойнхаузене (NRW,
Kreis Minden-Lübbecke).

> ⚠ Это не юридическая консультация. Факты собраны из официальных источников
> (ссылки внизу), но перед регистрацией деятельности обязательна проверка:
> (а) отметки в вашем Zusatzblatt к ВНЖ, (б) консультация в Ausländerbehörde
> Kreis Minden-Lübbecke и в STARTERCENTER NRW (бесплатно).
> Пометка [v] = подтверждено официальным источником; [~] = из практических
> руководств, желательно перепроверить под вашу ситуацию.

---

## 1. Правовой статус: что уже можно

- [v] Временная защита ЕС продлена **до 04.03.2027**; действующие ВНЖ по §24
  продолжают действовать автоматически (Fortgeltungsverordnung), заявление на
  продление не требуется (BMI, март 2025).
- [v] ВНЖ по §24 с отметкой **«Erwerbstätigkeit erlaubt»** разрешает
  **самозанятость и предпринимательство без отдельного разрешения по §21**:
  Gewerbeanmeldung, freiberufliche Tätigkeit, учреждение UG/GmbH (IHK).
  → Проверьте формулировку в вашей карте/Zusatzblatt: нужна именно
  «Erwerbstätigkeit erlaubt» (включает самозанятость), а не только
  «Beschäftigung erlaubt» (только найм). Если стоит ограничение — запросить
  снятие в ABH.
- [~] Разработка ПО как деятельность может квалифицироваться и как
  **Freiberuf** (инженерная/IT-консалтинг, без Gewerbesteuer, регистрация
  через Finanzamt), и как **Gewerbe** (продукт/платформа с подписками —
  скорее Gewerbe). Для RouteHub с B2B-подписками ориентируйтесь на Gewerbe;
  финальную классификацию делает Finanzamt по Fragebogen zur steuerlichen
  Erfassung.

### Рекомендуемая последовательность (фаза 0 → первые деньги)

1. Проверка отметки о самозанятости в ВНЖ (5 минут, определяет всё).
2. **Einzelunternehmen через Gewerbeanmeldung** в Stadt Bad Oeynhausen
   (~€20–30, один визит) — не UG. Причины: ноль затрат на нотариуса и
   Jahresabschluss, совместимо с Bürgergeld-механикой (Anlage EKS), быстро.
3. Fragebogen zur steuerlichen Erfassung (ELSTER) → Steuernummer, статус
   **Kleinunternehmer** (см. §4) — счета без НДС.
4. UG/GmbH — **позже**, при первом инвесторе или MRR > ~€2–3 тыс./мес
   (ограничение ответственности станет важнее простоты).

## 2. Bürgergeld, страховка и совместимость с бизнесом

- [~] Самозанятость **совместима с Bürgergeld**: доход декларируется через
  **Anlage EKS** (предварительная + итоговая), Jobcenter засчитывает прибыль
  с учётом Freibeträge и доплачивает разницу (Firmenhilfe, Handbook Germany).
  Практический смысл: первые месяцы низкого дохода не обнуляют базовый доход
  и **медстраховку продолжает оплачивать Jobcenter**.
- [~] **Einstiegsgeld** (§16b SGB II): добровольная доплата Jobcenter при
  выходе из Bürgergeld в самозанятость — ориентировочно €50–450/мес до
  24 мес., по усмотрению кейс-менеджера; подавать **до** начала деятельности,
  с бизнес-планом (этот пакет документов подходит как основа).
- [v] **Gründungszuschuss — НЕ ваш инструмент**: он привязан к ALG I
  (остаток права ≥150 дней), получателям Bürgergeld недоступен
  (Bundesagentur für Arbeit).
- [~] При выходе из Bürgergeld в полную самозанятость: взносы на
  медстраховку платите сами (GKV для самозанятых, минимум ~€250–300/мес) —
  заложить в финплан момент перехода.

## 3. Финансирование: реалистичная лестница

| Инструмент | Сумма | Условия / статус для §24 |
| --- | --- | --- |
| **Einstiegsgeld** (Jobcenter Minden-Lübbecke) | ~€50–450/мес ≤24 мес. | [~] дискреционно; подать до старта; нужен бизнес-план |
| **Gründungsstipendium.NRW** | **€1 200/мес × 12 мес.** | [v] соло-фаундеры ок; заявка через аккредитованную сеть; для не-ЕС нужен ВНЖ, действующий **на весь период** и разрешающий самозанятость как основную занятость — с §24 (до 03.2027) окно для 12-месячного гранта ещё открыто, но сужается: **подавать как можно раньше** |
| **EXIST-Gründungsstipendium** (федеральный) | €2 500/мес + до €10 тыс. Sachmittel + €5 тыс. коучинг, 12 мес. | [v] открыт гражданам третьих стран с любым действующим ВНЖ; требует привязки к вузу (диплом <5 лет или зачисление) — реалистично через Uni Bielefeld / Uni Paderborn (garage33) |
| Pre-seed (angel/фонды) | €150–250 тыс. | после первых метрик пилота; Founders Foundation — вход в OWL-нетворк |

Экосистема OWL рядом:

- **Founders Foundation** (Билефельд, ~45 км): бесплатные акселерационные
  программы, без барьера по статусу ВНЖ, и это аккредитованная сеть для
  Gründungsstipendium.NRW. → Первый внешний контакт, который стоит сделать.
- **garage33 / Uni Paderborn** (Excellence Start-up Center NRW) — путь к EXIST.
- **STARTERCENTER NRW** (при IHK Ostwestfalen) — бесплатная консультация по
  Gewerbe/налогам/грантам, есть опыт с фаундерами-беженцами.

## 4. Налоги и оформление продукта (коротко)

- [v] **Kleinunternehmerregelung с 01.01.2025**: до **€25 000** оборота в
  прошлом году и до **€100 000** в текущем (жёсткий потолок — при превышении
  статус теряется немедленно), суммы нетто; счета без НДС с пометкой об
  освобождении (§19 UStG; IHK München, Finanzamt NRW). Для B2B-подписок
  RouteHub на старте — идеально (немецкие заведения получают счёт без НДС).
- [v] **Impressum по §5 DDG** (заменил TMG с 14.05.2024) обязателен для сайта
  и приложения: имя, адрес, e-mail; штрафы до €50 тыс. Домашний адрес можно
  заменить Impressum-сервисом, если не хотите публиковать.
- [v] **DSA**: как микропредприятие (<50 сотрудников, <€10 млн) RouteHub
  освобождён от большинства платформенных обязанностей, но базовые остаются:
  контактная точка, понятные ToS, механизм notice-and-action для жалоб на
  UGC-контент (POI/отзывы) — заложить в Phase 1 roadmap.
- [v] **GDPR-геолокация**: разрешение ОС ≠ согласие по GDPR; согласие до
  инициализации SDK, гранулярно по целям (EDPB). Наш продукт уже устроен
  правильно (нет фонового трекинга, только явные чек-ины) — зафиксировать
  это в Datenschutzerklärung как принцип.

## 5. Стратегия ВНЖ на горизонте 2027

Защита по §24 заканчивается 04.03.2027 (если не продлят снова). Треки выхода
(все — со сменой статуса **без выезда из Германии**, §39 AufenthV; BAGFW 2026):

1. **§21 AufenthG (самозанятость)** — целевой трек, если RouteHub взлетит:
   нужны жизнеспособность бизнеса (бизнес-план, финансирование, экономический
   интерес региона) и обеспеченность средствами. Работающий продукт + грант
   NRW + первые B2B-клиенты = сильное досье.
2. **§18a/§18b (Fachkraft)** — запасной трек: senior-разработчик легко
   проходит по квалификации; можно комбинировать найм part-time +
   selbständige Nebentätigkeit (RouteHub как side-business с разрешением ABH).
3. **Niederlassungserlaubnis** — по накоплению лет пребывания/взносов
   (сроки зависят от трека; уточнить в ABH заранее, время по §24
   засчитывается не во все варианты [~]).

**Рекомендация**: не позже осени 2026 сходить в ABH с вопросом «какой трек вы
видите для меня» — решение по §21 готовится месяцами, и его лучше запускать
из действующего §24, а не в последний момент.

## 6. План действий на 90 дней

| Неделя | Действие |
| --- | --- |
| 1 | Проверить Zusatzblatt; записаться в STARTERCENTER NRW (IHK OWL) |
| 1–2 | Заявка на консультацию в Founders Foundation; спросить про аккредитацию для Gründungsstipendium.NRW |
| 2–3 | Einstiegsgeld: разговор с кейс-менеджером Jobcenter ДО регистрации Gewerbe |
| 3–4 | Gewerbeanmeldung (Stadt Bad Oeynhausen) + ELSTER Fragebogen (Kleinunternehmer) |
| 4–8 | Заявка на Gründungsstipendium.NRW через сеть; параллельно — пилот Bad Oeynhausen (см. [business-plan-de.md](business-plan-de.md)) |
| 8–12 | Первые 10 B2B-разговоров с заведениями Kurgebiet; фиксация метрик для досье §21 |

---

## Источники

- BMI — Änderung bei Einreise und Aufenthalt für Schutzsuchende aus der Ukraine (продление до 04.03.2027): bmi.bund.de
- BAGFW/asyl.net — Arbeitshilfe «Geflüchtete aus der Ukraine, Aufenthaltsverfestigung» (05.2026): bagfw.de
- IHK Koblenz — Selbständige Tätigkeit für ukrainische Geflüchtete: ihk.de/koblenz
- Handbook Germany — Ukraine: Jobcenter, Bürgergeld und Selbständigkeit: handbookgermany.de
- Firmenhilfe — Bürgergeld für Selbstständige (Anlage EKS): firmenhilfe.org
- Bundesagentur für Arbeit — Gründungszuschuss: arbeitsagentur.de
- Gründungsstipendium.NRW — FAQ + NRW.BANK product page: gruendungsstipendium.nrw, nrwbank.de
- EXIST-Gründungsstipendium (BMWK): exist.de
- Founders Foundation Bielefeld: foundersfoundation.de
- IHK München / Finanzamt NRW — Kleinunternehmerregelung 2025: ihk-muenchen.de, finanzamt.nrw.de
- §5 DDG (Impressum): gesetze-im-internet.de/ddg
- EDPB Guidelines 04/2020 (location data): edpb.europa.eu
- Minor — Aufenthaltsrechtliche FAQ für Menschen aus der Ukraine: minor-kontor.de
