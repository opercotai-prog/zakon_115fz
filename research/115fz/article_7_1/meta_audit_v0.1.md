# Meta-Audit v0.1

## 1. Purpose

Этот meta-audit проверяет, какие замечания в [research/115fz/article_7_1/audit_v0.1.md](research/115fz/article_7_1/audit_v0.1.md) отражают действительно универсальные проблемы схемы анализа юридической нормы, а какие относятся к особенностям конкретной нормы в [research/115fz/article_7_1/paragraph_3_1.txt](research/115fz/article_7_1/paragraph_3_1.txt).

Цель — не исправлять текущий аудит и не менять существующую схему, а отделить:

- фундаментальные ограничения модели;
- локальные особенности этой нормы;
- предложения, которые пока преждевременны для универсального схемного добавления.

При этом исходные ограничения эксперимента соблюдаются: работа только с текущим текстом, без внешнего юридического чтения статьи 48, без навязывания новой схемы.

---

## 2. Evaluation of SCHEMA_CHANGE_PROPOSALS

### CHANGE 1 — QUANTIFIER / OBJECT
- Current element: QUANTIFIER / OBJECT
- Problem: смешение количественной характеристики, объекта и квалификатора внутри одной синтаксической группы; в этой норме это особенно заметно по сочетанию "всех случаев документированного отказа".
- Category: UNIVERSAL
- Why: явная модельная проблема существует в любом тексте, где объект имеет количественное ограничение и отдельный квалификатор. В одной норме это проявилось особенно ярко, но сам тип проблемы не уникален.
- Minimal change required: не обязательно новое поле; достаточно явно разграничивать quantity / qualifier / object_head / scope внутри существующего object-описания.
- Example of other norm type: "все документы по каждому заявлению..." или "все уведомления о каждом выявленном нарушении..." — там также легко перепутать квантор и квалификатор.

### CHANGE 2 — OBJECT_QUALIFIER / EXTERNAL_REFERENCE_OF_OBJECT
- Current element: CONDITION / EXTERNAL_REFERENCE / OBJECT
- Problem: часть внешней ссылки может входить в описание объекта как квалификатор типа события, а не как условие выполнения обязательства.
- Category: PREMATURE
- Why: в этой норме это выглядит важным, но на одном примере нельзя утверждать, что такая структура универсальна для всех юридических норм. В ряде норм внешняя ссылка является именно ссылкой на источник, а не частью объекта. Здесь риск есть, но доказательность пока недостаточна.
- Minimal change required: если схема будет уточняться, то минимально — хранить связь "reference -> object segment" без обязательного введения отдельного поля; не требовать нового универсального поля на текущем этапе.
- Example of other norm type: правило об уведомлении "по форме, установленной нормативным актом" может относиться либо к объекту, либо к условию, либо к форме действия; это требует отдельной проверки, но не доказывает универсального поля.

### CHANGE 3 — ACTION_CLUSTER / COMPOUND_ACTION
- Current element: ACTION
- Problem: несколько глаголов, соединённых союзом "и", могут быть компонентами одного обязательства, а не двумя отдельными действиями.
- Category: UNIVERSAL
- Why: это общее структурное свойство нормативных текстов: одно обязательство может быть описано набором глаголов с общим объектом, сроком и адресатом. Проблема не зависит от статьи 48 и появляется в иных нормах.
- Minimal change required: добавить возможность модели описывать compound action / action cluster как единый акт с несколькими компонентами, не превращая его автоматически в два самостоятельных действия.
- Example of other norm type: "представлять и хранить информацию"; "подписывать и направлять документы"; "вносить и подтверждать сведения" — все это типовые случаи составного обязательства.

### CHANGE 4 — DEADLINE_ANCHOR / TEMPORAL_REFERENCE
- Current element: DEADLINE / DEADLINE_START / TRIGGER
- Problem: срок привязан не только к количеству дней, но и к событию отсчёта: "следующих за днем принятия решения".
- Category: UNIVERSAL
- Why: различие между сроком, событием отсчёта и триггером обязательства является фундаментальным для любого юридического текста. Для текущей нормы это особенно заметно, но тип проблемы общий.
- Minimal change required: не обязательно новое поле в каждом тексте, но нужна явная модельная возможность фиксировать temporal anchor / deadline reference отдельно от trigger.
- Example of other norm type: "в течение 10 дней со дня получения уведомления", "не позднее дня, следующего за датой принятия решения" — это стандартная временная привязка.

### CHANGE 5 — разделение CONDITION и EXTERNAL_REFERENCE
- Current element: CONDITION / EXTERNAL_REFERENCE / LEGAL_DEPENDENCY
- Problem: условие, внешняя ссылка и ограничитель объекта легко смешиваются, особенно когда ссылка входит в описание объекта.
- Category: UNIVERSAL
- Why: даже без внешней юридической интерпретации это типичная модельная проблема. Текст может содержать и условие, и ссылку, и описание объекта одновременно; эти роли должны быть различимы.
- Minimal change required: не обязательно создавать новое поле, но нужна точная семантическая разграниченность: condition vs reference vs qualifier, с возможностью сочетания нескольких ролей в одной фразе.
- Example of other norm type: "при наличии основания, предусмотренного ..."; "в соответствии с порядком, установленным ..." — ссылки и условия часто переплетаются.

---

## 3. Evaluation of NEEDS_REFINEMENT

### Item: separate object and qualifiers
- Current element: OBJECT
- Problem: объект смешан с ограничителями и квалификаторами.
- Category: UNIVERSAL
- Why: любой юридический текст может содержать объект, ограничения по признакам, внешние ссылки и количественные рамки в одной фразе. На этой норме это заметно, но сама проблема общая.
- Minimal change required: внутри OBJECT хранить выделенные части: object_head, quantity_scope, qualifier, reference-to-object.
- Example of other norm type: "сведения обо всех случаях ... в отношении ... по основанию ..." — типичное многослойное объектное описание.

### Item: separate external reference from condition
- Current element: CONDITION
- Problem: ссылка на внешнюю норму трактуется как условие применения, хотя в тексте она может быть квалификатором объекта.
- Category: PREMATURE
- Why: проблема корректная и значимая, но по одному тексту нельзя сделать вывод, что все внешние ссылки должны всегда отделяться от условия. Для универсальной модели это не доказано.
- Minimal change required: добавить гибкую связь "reference -> described element" и не заставлять все ссылки становиться условиями.
- Example of other norm type: определение формы или содержания документа через ссылку на иной акт.

### Item: action cluster
- Current element: ACTION
- Problem: необходимость хранить составное действие как единый акт с общими параметрами.
- Category: UNIVERSAL
- Why: составное действие — типичное конструкционное явление в нормативном языке; текущая норма только иллюстрирует это.
- Minimal change required: allow action groups without forcing decomposition into two independent obligations.
- Example of other norm type: "представлять и хранить"; "подписывать и направлять".

### Item: distinction condition vs object restriction
- Current element: CONDITION / SCOPE
- Problem: фраза может ограничивать тип объекта, а не создавать отдельное условие правового действия.
- Category: UNIVERSAL
- Why: это фундаментальная проблема представления логики нормы: часть текста может быть и квалификатором объекта, и косвенным условием, но не обязательно быть условием применения.
- Minimal change required: distinguish object restriction from condition; maintain both relations without collapsing them.
- Example of other norm type: "сведения о случаях отказа при наличии основания ...".

### Item: deadline anchor
- Current element: DEADLINE_START / TRIGGER
- Problem: событие отсчёта срока должно быть отделено от trigger отношения.
- Category: UNIVERSAL
- Why: различие между trigger и anchor является общим для сроков во многих нормах.
- Minimal change required: capture anchor as temporal reference, not necessarily as trigger.
- Example of other norm type: "в течение 5 рабочих дней со дня получения уведомления".

---

## 4. Evaluation of MISSING

### Item: object qualifier
- Current element: OBJECT
- Problem: нет явного способа сохранять квалификатор объекта отдельно от количества и основного объекта.
- Category: UNIVERSAL
- Why: это общий недостаток, когда объект прилагателен/квалифицирующий и количественно ограничен одновременно.
- Minimal change required: allow sub-structure within object description.
- Example of other norm type: "информация о всех выявленных нарушениях, связанных с ...".

### Item: common object for multiple verbs
- Current element: ACTION
- Problem: нет явного представления, что несколько глаголов относятся к одному объекту и одному сроку.
- Category: UNIVERSAL
- Why: это не уникально для этой нормы; в нормативных текстах часто встречается один объект для нескольких глаголов.
- Minimal change required: support grouped action with shared object/deadline.
- Example of other norm type: "формировать и представлять отчётность".

### Item: external reference as formal basis
- Current element: EXTERNAL_REFERENCE
- Problem: reference needs a way to mark that it qualifies an object or event without saying it is a condition.
- Category: PREMATURE
- Why: this is a plausible general need, but on current evidence it is not proven that all references must be formalized in the same way.
- Minimal change required: a light-weight reference-to-segment relation rather than a new mandatory field.
- Example of other norm type: references to forms, registries, procedures or acts in administrative rules.

### Item: separate deadline anchor
- Current element: DEADLINE_START
- Problem: no explicit temporal anchor separate from trigger.
- Category: UNIVERSAL
- Why: this is general and not specific to the law text under review.
- Minimal change required: add temporal anchor metadata to deadline.
- Example of other norm type: "не позднее следующего рабочего дня после получения решения".

---

## 5. Evaluation of REDUNDANT

### Item: CONDITION and LEGAL_DEPENDENCY overlap
- Current element: CONDITION / LEGAL_DEPENDENCY
- Problem: the same phrase may be captured both as a condition and as legal dependency.
- Category: REDUNDANT
- Why: this is not a reason to add a new field; it is a modeling discipline issue. Existing fields can be used with clearer role assignment.
- Minimal change required: clarify semantics, not add a new element.
- Example of other norm type: references in other rules may equally fit condition or legal dependency depending on how they are modeled; this does not mean the schema needs a third category.

### Item: SCOPE and QUANTIFIER overlap
- Current element: SCOPE / QUANTIFIER
- Problem: both may describe the same limit of a case set.
- Category: REDUNDANT
- Why: the overlap is already explainable by one concept being quantitative and the other structural. This does not require a new element; it requires more precise assignment.
- Minimal change required: clarify the difference between scope and quantifier; keep the same fields.
- Example of other norm type: "все документы" or "в пределах каждого случая".

### Item: ACTION and action cluster duplication
- Current element: ACTION
- Problem: if the system introduces a cluster field, it may duplicate the same information already tracked as multiple actions.
- Category: REDUNDANT
- Why: duplication risk exists only if the schema adds separate fields without controlled semantics. This is more a schema governance problem than a universal field requirement.
- Minimal change required: alternative representation, not new standalone field by default.
- Example of other norm type: broad administrative reporting duties that combine several verbs in one requirement.

---

## 6. Evaluation of DANGEROUS

### Item: external reference treated as condition
- Current element: CONDITION / EXTERNAL_REFERENCE
- Problem: reference is elevated to a condition of applicability without explicit proof from current text.
- Category: UNIVERSAL
- Why: this is a general anti-pattern in legal modeling. Mixed expressions of reference and condition are common across legal texts and can produce false legal conclusions.
- Minimal change required: do not infer condition from reference without explicit text or external source; keep them distinct.
- Example of other norm type: rules that say "в соответствии с порядком, установленным ..." are not necessarily conditions of applicability.

### Item: collapse of object into a single blob
- Current element: OBJECT
- Problem: several semantic layers are merged into one object.
- Category: UNIVERSAL
- Why: this issue is not limited to one norm; it is a frequent source of bad extraction.
- Minimal change required: preserve object segmentation and allow qualifiers / references / cases as separate nested nodes.
- Example of other norm type: any object containing subject, event, basis and source in one phrase.

### Item: qualifier misread as quantifier
- Current element: QUANTIFIER
- Problem: adjectives like "документированный" are treated as quantity markers.
- Category: UNIVERSAL
- Why: this is a general linguistic error; legal texts often use qualifiers that are not quantifiers.
- Minimal change required: maintain strict distinction between quantities, descriptors and qualifiers.
- Example of other norm type: "письменное уведомление", "обоснованное решение", "первичная информация" — description, not quantity.

### Item: same deadline for each action
- Current element: ACTION / DEADLINE
- Problem: if two verbs are treated as separate obligations with separate deadlines, the model may become too rigid.
- Category: NORMA_SPECIFIC
- Why: in this norm the text gives one shared deadline to one overall duty, but this exact pattern does not prove that all multi-verb duties share the same deadline. It is a local textual fact before becoming a universal schema concern.
- Minimal change required: keep one shared deadline unless the text explicitly assigns separate deadlines.
- Example of other norm type: in some norms, a composite duty may indeed have different deadlines for each component; the schema should not assume uniformity.

---

## 7. Universal Problems

### Проблемы, которые можно считать устойчивыми на текущем эксперименте

1. Разделение квантора, квалификатора и объекта является устойчивой модельной задачей.
2. Одно правило может содержать составное действие с общим объектом и общим сроком.
3. Срок должен фиксироваться вместе с его точкой отсчёта, а не только как число и единица времени.
4. Внешняя ссылка и условие применения — это разные роли и их нельзя автоматически отождествлять.
5. Конструкция объекта может содержать несколько смысловых уровней, которые необходимо сохранять отдельно.

These are not merely local problems of paragraph 3.1; they are structural risks for any extraction model aimed at legal norms.

---

## 8. Norma-Specific Problems

### Проблемы, которые в основном следуют из особенностей конкретной нормы

1. Формула "сведения обо всех случаях документированного отказа ..." создаёт особенно сложный объект, потому что внутри неё соединены: предмет предоставления, множество случаев, тип отказа и внешняя правовая ссылка.
2. Сочетание "все случаи" и "документированного отказа" усиливает путаницу между количественным ограничением и качественным описанием.
3. В этой норме два глагола имеют общий объект, адресат и срок, поэтому проблема compound action проявляется особенно заметно. Это не означает, что все нормы со множеством глаголов обязаны быть составными в одинаковой форме.
4. Временной фрагмент "следующих за днем принятия решения" даёт очень конкретную временную привязку, но именно она делает различие между trigger и deadline anchor особенно заметным.

---

## 9. Premature Changes

### Предложения, которые логически интересны, но пока слишком рано вводить как обязательные элементы схемы

1. OBJECT_QUALIFIER / EXTERNAL_REFERENCE_OF_OBJECT
   - Reason: may be useful, but one norm is insufficient to prove necessary universal structure.
   - Risk: overfitting to one syntactic pattern.

2. Strict separation of CONDITION and EXTERNAL_REFERENCE as separate mandatory fields for every case
   - Reason: in some rules external reference is only a part of the object description, not a condition.
   - Risk: force a false distinction across different legal styles.

3. Mandatory ACTION_CLUSTER field for every multi-verb sentence
   - Reason: helpful, but not every multi-verb sentence is a compound duty; some are just multiple coordinated acts on a common object.
   - Risk: too rigid schema for naturally written legal text.

These should be kept as design options for the next round of experiments, not as fixed universal fields.

---

## 10. Recommended Next Experiment

Следующая проверочная норма должна быть выбрана так, чтобы она позволила отделить универсальные и локальные эффекты.

### Требуемые свойства следующей тестовой нормы

1. Норма с несколькими глаголами, но одним объектом, одним адресатом и одним сроком.
2. Норма с внешней ссылкой, встроенной в описание объекта, а не в отдельное условие.
3. Норма со сроком, имеющим явную точку отсчёта и не совпадающую с trigger.
4. Норма с количественным ограничителем и квалификатором, которые не совпадают семантически.
5. Норма, где условие применения и ограничение объекта различаются syntactically.
6. Норма без явного исключения, чтобы отделить "проблему отсутствия исключения" от "проблемы неправильного смешения ролей".

Цель следующего эксперимента — не доказать, что конкретный элемент должен существовать везде, а проверить, устойчив ли он в нескольких разных юридических конструкциях.

---

### Short conclusion

- Что уже можно считать устойчивой проблемой схемы: смешение квантора, квалификатора и объекта; необходимость различать condition и external reference; необходимость различать trigger и temporal anchor; проблема compound action с общим объектом.
- Что пока нельзя считать доказанной проблемой: введение новых обязательных универсальных полей типа OBJECT_QUALIFIER, EXTERNAL_REFERENCE_OF_OBJECT или ACTION_CLUSTER без проверки на более чем одной норме.
- Какие свойства должна иметь следующая тестовая норма: множественные глаголы, внешняя ссылка внутри объекта, срок с anchor, квантор и квалификатор в одном фрагменте, а также разница между условием и ограничением объекта.

---

## Final assessment

В текущем эксперименте уже видно, что схема должна быть более точной в отношении структурного различия между:

- объектом;
- ограничением объекта;
- квантором;
- квалификатором;
- ссылкой на внешний источник;
- условием;
- trigger;
- временной привязкой срока.

Но новые поля стоит вводить осторожно. На основании одной нормы допустимо фиксировать только то, что эти различия реально важны, а не то, что они обязательно должны быть оформлены одинаково во всех случаях.
