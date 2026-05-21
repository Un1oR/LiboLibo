# Audit: текущий процесс, session logs и guardrails

**Дата:** 2026-05-19  
**Статус:** артефакт расследования  
**Источник:** пункт 1 из `docs/specs/2026-05-19-project-state-android-and-agent-flow-investigation.md`

## Summary

Механика `docs/sessions` появилась уже в первом commit репозитория как конвенция документации. После проверки YouTube-стрима стало понятно, что это не просто самостоятельная фантазия Claude: примерно на `01:15-01:32` от начала стрима Илья, Самат и Егор явно обсуждают разработку через документацию рядом с кодом, открытый GitHub-репозиторий, сохранение ТЗ/важных обсуждений, последующее логирование и разделение `specs` / `sessions`. Claude интерпретировал этот разговор в конкретную структуру `docs/sessions` и `docs/specs`, а обязательным правилом для агентов она стала позже, когда был добавлен `CLAUDE.md` в commit `0456ce2`.

`SECURITY.md` появился почти сразу после kickoff в commit `d87f99e` по прямой просьбе Ильи "подумать о безопасности" для публичного репозитория. Базовый запрет на secrets, leak response и stream hygiene остаются полезными guardrails, но текущий `SECURITY.md` смешивает несколько слоев: публичную security policy GitHub-репозитория, правила для стримов, инструкции агенту перед commit и куски продуктовой архитектуры секретов. Это стоит разделить концептуально, даже если физический файл пока оставить как есть.

Самый жесткий ритуал завершения iOS-задач - `build -> simulator -> commit -> push` - появился в commit `9bfb759`, и для него есть прямое evidence, что это попросил Илья.

Для Android-старта это значит: полезно сохранить трассируемость решений, specs и fresh verification, но нельзя буквально переносить iOS-ритуал. Android нужен собственный repeatable feedback loop, а правила commit/push, нумерации session logs и "свежего лога" стоит сделать зависимыми от типа работы и трека.

## Подтвержденные факты

- `docs/sessions` существует с первого commit `cdbc2a4` от 2026-04-25. Первый лог: `docs/sessions/2026-04-25-kickoff.md:1`; в нем указано, что документ составлен Claude по расшифровке и заметкам Granola.
- В первом `docs/README.md:7` уже описаны `sessions/`, `specs/` и правило, что каждая сессия документируется. Это еще не `CLAUDE.md` и не строгий agent-rule.
- YouTube-стрим `mKjCHo7GKko` подтверждает момент зарождения процесса. Локальный ASR на Parakeet V3 для участка `01:15:00-01:35:00` показывает: сначала Илья просит Claude взять разговор из Granola и составить ТЗ на первый шаг; затем Егор предлагает сохранять важную спецификацию файлами в `docs`, чтобы агент мог перечитывать контекст; затем формулируется открытый repo с папкой документации, куда складывается текущий текст и будущие материалы; после создания repo участники отдельно обсуждают появившиеся `sessions` и `specs`.
- `SECURITY.md` впервые появляется в `d87f99e` вместе с `docs/sessions/2026-04-25-02-corrections.md`. Session log прямо говорит, что Илья попросил "подумать о безопасности" при работе с публичным репозиторием; Claude создал `SECURITY.md`, усилил `.gitignore`, зафиксировал stream hygiene и обещание сканировать staging-area перед commit.
- Текущий `SECURITY.md` содержит: запрет secrets/PII/internal logs, хранение secrets для iOS/backend, HTTPS/logging rules, поведение на стримах, leak response, упоминание GitHub Secret Scanning, локальный grep/gitleaks, private contact. `CLAUDE.md` ссылается на него как на краткое security rule для агентов.
- GitHub Docs описывает `SECURITY.md` как community-health/security-policy файл для инструкций по reporting vulnerabilities; такие файлы поддерживаются в `.github`, root или `docs` folder. Поэтому root-level placement сам по себе не аномалия, но широкий процессный контент в нем не обязан жить.
- `docs/specs` как путь впервые появляется в `d87f99e` с `podcasts-feeds.json`. Первая полноценная техническая спека появляется в `ef01c99`: `docs/specs/step-01-ios-skeleton.md`.
- `CLAUDE.md` впервые добавлен в `0456ce2` 2026-04-25. В нем session logs и specs становятся обязательным правилом для AI-ассистентов: `CLAUDE.md:9`, `CLAUDE.md:62`.
- В `9bfb759` `CLAUDE.md` меняет политику commit'ов: старая осторожная политика "не делай коммитов без явной просьбы" заменяется на "сама просьба сделать задачу = просьба собрать и запушить". Объяснение зафиксировано в `docs/sessions/2026-04-25-16-podcasts-alphabetical-sort.md:13`.
- `AGENTS.md` появляется только 2026-05-19 в `eeabf83`; он добавляет инструкцию учитывать ошибки voice transcription.
- Локальные Superpowers-like skills добавлены тем же `eeabf83`, поэтому они не могли быть историческим источником апрельских `session logs` и `CLAUDE.md`.

## Интерпретации и гипотезы

- Первичная механика session logs теперь выглядит как смесь явного человеческого запроса и агентской конкретизации. Люди сформулировали документацию рядом с кодом, сохранение ТЗ/важных обсуждений и последующее логирование; Claude превратил это в конкретные `docs/sessions` и `docs/specs`.
- Разделение именно на `sessions` и `specs` похоже на локальную интерпретацию Claude, но оно было замечено на стриме и не было отклонено: участники отдельно обсуждали, не лишние ли `sessions`, и оставили схему как приемлемую.
- `SECURITY.md` имеет сильный source: это direct human prompt плюс агентская конкретизация. В отличие от `sessions/specs`, здесь не надо гадать, была ли исходная просьба: она зафиксирована в session 02.
- Root-level `SECURITY.md` стоит считать нормальным местом для public-facing политики: куда писать о vulnerability, что не класть в публичный repo, что делать при leak. Но правила "что агент должен проверить перед commit", подробности стримов и продуктовые threat-model решения лучше держать в других слоях, чтобы `SECURITY.md` не становился универсальным договором для всех.
- Обязательность в `CLAUDE.md` скорее была предложена или закреплена агентом во время backend-kickoff: commit message говорит, что AI-ассистенты подхватывают это автоматически, а session log фиксирует добавление `CLAUDE.md`.
- Ритуал iOS-завершения имеет сильный источник: явная просьба Ильи зафиксирована в session log 16.
- Новые Superpowers-like правила от 2026-05-19 являются текущим рабочим слоем для расследования Android/agent-flow, но не историческим источником апрельского процесса.

## Timeline

| Дата / commit | Что появилось или изменилось | Evidence |
|---|---|---|
| 2026-04-25 stream `~01:15-01:32` | Проговорена разработка через документацию рядом с кодом: ТЗ из Granola, файлы в `docs`, открытый repo, последующее логирование, обсуждение `sessions` / `specs`. | YouTube `mKjCHo7GKko`; локальный ASR Parakeet V3, chunks `0000-0003`, `0011-0013`, `0032`, `0039-0040` from `01:15:00-01:35:00` |
| 2026-04-25 `cdbc2a4` | Initial repo, `docs/README.md`, первый session log. `docs/README` уже задает `sessions/` и будущие `specs/`. | `docs/README.md:7`, `docs/sessions/2026-04-25-kickoff.md:3` |
| 2026-04-25 `d87f99e` | Первый файл в `docs/specs`: `podcasts-feeds.json`; corrections log; добавлен `SECURITY.md` и расширен `.gitignore` по прямой просьбе подумать о безопасности публичного repo. | `git show --stat d87f99e`, `docs/sessions/2026-04-25-02-corrections.md:40`, `SECURITY.md:1` |
| 2026-04-25 `ef01c99` | Первая полноценная спека: `step-01-ios-skeleton.md`; "каждая фаза - отдельный commit и session log"; DoD включает session log. | `docs/specs/step-01-ios-skeleton.md:26` |
| 2026-04-25 `17817fe` | Первый feature commit с session log и проверкой build/simctl. | `docs/sessions/2026-04-25-03-step-1.0.md:26` |
| 2026-04-25 `3b1db07` | Отказ от XcodeGen, `.xcodeproj` в repo, спека сжата. Ранний пример, что specs менялись вслед за реальностью. | `docs/specs/step-01-ios-skeleton.md:29` |
| 2026-04-25 `0456ce2` | Добавлен `CLAUDE.md`; session logs и specs стали обязательным agent-rule. | `CLAUDE.md:9`, `docs/sessions/2026-04-25-14-step-2-backend-kickoff.md:53` |
| 2026-04-25 `9bfb759` | Добавлен iOS completion ritual; снят запрет на commit без явной просьбы. | `docs/sessions/2026-04-25-16-podcasts-alphabetical-sort.md:13` |
| 2026-04-25 `053ccbd` | `CLAUDE.md` обновлен под bundle id `test.libolibo.ru`; смысл правил не менялся. | `CLAUDE.md:73` |
| 2026-05-19 `eeabf83` | Добавлены `AGENTS.md`, Android investigation spec, локальные skills. | `AGENTS.md:1`, `docs/specs/2026-05-19-project-state-android-and-agent-flow-investigation.md:28`, `skills-lock.json:4` |

## Inventory Guardrails

| Правило | Возможный источник | Доказанность | Текущая польза | Стоимость / риск |
|---|---|---:|---|---|
| Каждая сессия имеет log в `docs/sessions` | Человеческий запрос на документацию/logging + Claude конкретизировал в `sessions` | Высокая для происхождения, средняя для точного формата | Хорошая историческая трассировка решений | Шум, много логов за один день, риск "лог ради лога" |
| Session log обязателен для каждой работы | `CLAUDE.md` в `0456ce2`, вероятно агент закрепил как repo-rule | Высокая для факта, низкая для источника | Помогает агентам восстанавливать контекст | Плохо масштабируется на мелкие правки и параллельные ветки |
| Specs в `docs/specs` для больших документов | Stream discussion about saving specs/plans in docs + `docs/README` initial + `CLAUDE.md` | Высокая | Полезно для Android proposal и API/data contracts | Specs могут устаревать, если не отмечать статус |
| "Прочитай свежий session log и актуальную spec в начале" | `CLAUDE.md` | Высокая | Полезно для continuity | "Свежий" может быть нерелевантен при параллельных треках |
| iOS: build -> install -> launch | Явная просьба Ильи в session 16 | Высокая | Хорошо для iOS confidence loop | Не переносится на Android; команды и simulator name устаревают |
| После задачи commit + push без отдельного подтверждения | Явная просьба Ильи в session 16 | Высокая | Ускоряло публичный vibe-coding поток | Конфликтует с dirty worktree, PR-flow, research/WIP и безопасной работой агента |
| Не смешивать iOS и backend без нужды | `CLAUDE.md`, локальная дисциплина слоев | Средняя | Все еще полезно | Для Android/backend contract может мешать, если трактовать слишком жестко |
| Русский язык документации, английские technical terms | `CLAUDE.md` | Высокая | Актуально для команды и voice context | Низкая стоимость |
| Root `SECURITY.md` как public no-secrets/vulnerability policy | Прямая просьба Ильи + Claude concretization в `d87f99e`; GitHub community-health convention | Высокая | Критично для публичного repo, stream и внешних reports | Риск превращения в catch-all для агентских и продуктовых правил |
| Без secrets, `.env`, Railway vars в repo | Corrections/backend sessions + security rules | Высокая | Критично | Сохранить; enforcement должен быть машинно проверяемым, а не только текстовым |
| Stream hygiene: не показывать `.env`, rotate immediately | Session 02 + `SECURITY.md` | Высокая | Важна именно для публичной разработки/стримов | Лучше как короткий runbook в `docs/process`/`docs/runbooks`, а не только в root policy |
| Agent pre-commit secret check | Session 02: "буду быстро сканировать staging-area"; `SECURITY.md` grep/gitleaks | Средняя | Полезно, если реально выполняется | `grep` по staged diff слабый и шумный; лучше gitleaks/pre-commit/CI или отдельный agent skill |
| iOS Keychain / backend env vars как secret storage rule | `SECURITY.md`, backend specs/sessions | Средняя | Правильное направление: provider secrets не в клиенте, server secrets в env | Формулировка "iOS secrets in Keychain" слишком общая: публичный клиент не может безопасно хранить provider secrets; Keychain годится для user/device tokens |
| "Каждая подфаза = отдельная сессия + спека/дополнение" | Backend step spec | Высокая | Полезно для крупных фаз | Избыточно для маленьких vertical slices |
| Superpowers/TDD/verification skills | Добавлены 2026-05-19 из `obra/superpowers` | Высокая для текущего наличия | Полезно для Android automation-first | Требуют адаптации к локальному процессу и путям |

## Что оставить

- `docs/specs` для Android-start proposal, API boundaries, data provider contracts и устойчивых архитектурных решений.
- Session logs как decision log для существенных работ: архитектура, deploy, API, payment/account model, процессные правила.
- Fresh verification перед claim'ами, но платформенно: Android должен иметь свою команду проверки, а не iOS-specific ritual.
- Root `SECURITY.md` как компактную публичную security policy: reporting contact, no-secrets baseline, leak response, ссылки на более подробные internal/process docs.
- Security rules и запрет secrets, но с упором на enforceable checks: `.gitignore`, GitHub Secret Scanning/push protection status, gitleaks/pre-commit/CI там, где это реально включено.

## Что пересмотреть

- `CLAUDE.md` описывает репозиторий как "iOS + backend", без Android. Для Android-start это устаревшая рамка.
- iOS ritual привязан к `iPhone 17`, `xcodebuild`, `simctl`, bundle id. Для Android он не годится как общее правило.
- Auto `commit + push` слишком сильное default-правило. Для research, PR review, незакоммиченного рабочего слоя и Android scaffolding лучше требовать явного намерения или отдельный режим.
- Нумерация session logs уже ломалась: есть дубликаты `2026-04-25-14` и параллельные номера. `NN` как глобальный порядок плохо проверяем.
- "Свежий лог" плохо определен при параллельных треках iOS/backend/Android. Лучше: "последний релевантный лог по треку + актуальная spec".
- `SECURITY.md` сейчас смешивает public policy, stream runbook, agent checklist и продуктовые storage rules. Более чистая раскладка:
  - root `SECURITY.md`: как сообщать о vulnerability, что не коммитить, что делать при leak;
  - `AGENTS.md`/локальный skill: как агент проверяет diff, что не печатает в output, какие команды запускает перед commit;
  - `docs/process` или `docs/runbooks`: правила стримов и incident response;
  - feature specs / ADR: конкретные product-security решения по Auth, Adapty, comments, Android signing.
- Проверить фактический статус GitHub Secret Scanning/push protection. В repo есть утверждение "включено", но локальный git сам это не доказывает.
- Уточнить формулировку про client secrets: Android/iOS не должны хранить server/provider secrets; Keychain/Keystore подходят для user/device tokens и public SDK config, но не превращают client-side secret в настоящий секрет.

## Evidence

- `cdbc2a4`: initial repo, kickoff session log, docs convention.
- YouTube stream `mKjCHo7GKko`, локальный ASR Parakeet V3, участок `01:15:00-01:35:00`: origin discussion for Granola -> ТЗ -> docs folder -> open repo -> logging -> `sessions` / `specs`.
- `d87f99e`: `SECURITY.md`, `.gitignore` strengthening, corrections log after explicit security request.
- `ef01c99`: первая `docs/specs/step-01-ios-skeleton.md`, phase/log discipline.
- `0456ce2`: первый `CLAUDE.md`, обязательные session logs/specs.
- `9bfb759`: iOS completion ritual, explicit human request evidence.
- `053ccbd`: bundle id update in ritual.
- `eeabf83`: `AGENTS.md`, Android investigation, local skills.
- `CLAUDE.md:9`, `CLAUDE.md:62`, `CLAUDE.md:73`.
- `docs/README.md:7`.
- `docs/sessions/2026-04-25-02-corrections.md:40`.
- `docs/sessions/2026-04-25-kickoff.md:3`.
- `docs/sessions/2026-04-25-16-podcasts-alphabetical-sort.md:13`.
- `docs/specs/step-02-backend.md:241`.
- `SECURITY.md:3`, `SECURITY.md:17`, `SECURITY.md:24`, `SECURITY.md:36`, `SECURITY.md:49`.
- GitHub Docs, "Creating a default community health file": supported community health files can live in `.github`, root or `docs`; `SECURITY.md` gives vulnerability reporting instructions. <https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file>
- `skills-lock.json:4`.

## Пробелы

- В repo нет исходного Granola-транскрипта; stream-ASR подтверждает общий conversation flow, но не дает дословный исходный текст, который Claude получил из Granola.
- ASR сделан локально по YouTube-аудио через `scripts/transcribe_with_parakeet.py` и Handy Parakeet V3 cache. Распознавание шумное, поэтому evidence надо трактовать по таймкодам и смыслу, а не как дословную стенограмму.
- GitHub-side security settings не проверены через API/UI: локально видно только утверждение в `SECURITY.md` и session 02.
- В repo нет реального pre-commit/gitleaks/CI enforcement для secret scan; есть `.gitignore`, текстовая политика и рекомендация.
- Session 16 упоминает auto-memory, но agent memory не хранится в repo и не проверялась.
- Не проверялась удаленная GitHub/PR история за пределами локального `git log`.
- Публичные Claude Code / agentic-coding гайды не проверялись, потому что локального evidence достаточно для происхождения repo-правил.

## Последствия

- **Android:** завести отдельный Android completion ritual: Gradle build/test + затем emulator/instrumented smoke, без наследования iPhone-specific команд.
- **Android security:** с первого дня добавить Android-specific no-secrets boundary: keystore/google-services/private signing files не в repo; default tests не требуют production secrets; provider/server secrets только backend/env. Но не превращать root `SECURITY.md` в Android handbook.
- **Тесты:** Android-start должен закреплять проверяемую команду с первого vertical slice; session log не заменяет тестовый feedback loop.
- **Локальная разработка:** правила должны различать `iOS`, `api`, `android`, `docs/research`; auto-push не должен быть универсальным default.
- **Будущие правила:** перейти от "каждая сессия обязательно" к "каждое существенное решение/изменение имеет trace": короткий log для значимых работ, specs для устойчивых контрактов, explicit status для stale docs.
- **Security docs:** оставить root `SECURITY.md` как public entrypoint, а detailed operational/agent rules вынести в слой процесса или skills, когда будем реально переписывать guardrails.
