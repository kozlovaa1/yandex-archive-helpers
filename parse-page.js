(async function () {
    const SERVER_URL = "АДРЕС ВАШЕГО ОБРАБОТЧИКА";

    // Оверлей
    const overlay = document.createElement('div');
    overlay.style = "position:fixed;top:10px;right:1 0px;background:rgba(0,0,0,0.8);color:#fff;padding:15px;z-index:9 999;border-radius:5px;font-famil y:sans-serif;";
    overlay.innerHTML = "🔍 Анализ данных страницы...";
    document.body.appendChild(overlay);

    // 1. Парсим JSON с данными страницы
    let pageData = {};
    try {
        const nextDataScript = document.getElementById('__NEXT_DATA__');
        if (nextDataScript) {
            const json = JSON.parse(nextDataScript.innerText);

            // Ищем items в props.pageProps
            if (json.props && json.props.pageProps && json.props.pageProps.items) {
                // Создаем карту: parentId -> { pageNum: itemData }
                json.props.pageProps.items.forEach(item => {
                    if (item.parentId && item.sheetPageNumber !== undefined) {
                        if (!pageData[item.parentId]) {
                            pageData[item.parentId] = {};
                        }
                        // Сохраняем по номеру страницы (приводим к строке для надежности)
                        pageData[item.parentId][String(item.sheetPageNumber)] = item;
                    }
                });
                console.log(`🧠 Загружена структура дел: ${Object.keys(pageData).length} дел`);
            }
        }
    } catch (e) {
        console.error("Ошибка парсинга __NEXT_DATA__:", e);
    }

    // 2. Сбор элементов из DOM
    // Ищем карточки (разные варианты классов)
    let items = document.querySelectorAll('div[class*="Snippet-Body"]'); // Новый дизайн?
    if (!items.length) items = document.querySelectorAll('.Snippet'); // Старый дизайн
    if (!items.length) items = document.querySelectorAll('div[class*="Card_Card"]'); // Еще вариант

    if (!items.length) {
        overlay.innerHTML = "❌ Элементы списка не найдены!";
        setTimeout(() => overlay.remove(), 3000);
        return console.warn("Элементы списка не найдены. Проверьте селекторы.");
    }

    console.log(`🔎 Найдено элементов на странице: ${items.length}`);
    const results = [];

    for (let i = 0; i < items.length; i++) {
        const item = items[i];
        try {
            // Ищем заголовок
            let titleEl = item.querySelector('div[class*="Card_Title"]');
            if (!titleEl) titleEl = item.querySelector('.Snippet-Title');
            if (!titleEl) titleEl = item.querySelector('h3'); // Общий случай

            // Ищем ссылку
            let linkEl = item.querySelector('a[href*="/archive/catalog/"]');
            if (!linkEl) linkEl = item.querySelector('a');

            // Ищем мета-информацию (фонд, опись...)
            let metaEl = item.querySelector('div[class*="Text_TextSecondary"]');

            if (!titleEl || !linkEl) continue;

            const title = titleEl.innerText;
            const href = linkEl.href;
            const meta = metaEl ? metaEl.innerText : "";

            overlay.innerHTML = `⏳ Обработка ${i + 1}/${items.length}: ${title.substring(0, 20)}...`;

            let textContent = "";
            let realId = "";

            // Разбираем URL
            // Пример: /archive/catalog/PARENT_ID/PAGE_ NUM
            // /archive/catalog/840e6984-7833-4f96-8576-9c4c11b0e271/71
            const urlParts = href.split('/catalog/');

            if (urlParts[1]) {
                // Убираем параметры запроса (?...) и разбиваем по слэшам
                const pathSegments = urlParts[1].split('?')[0].split('/');

                // Логика:
                // Если сегментов 2 -> parentId / pageNum
                // Если сегментов 1 -> это само дело (без страницы)

                let parentId = "";
                let pageNum = "";

                if (pathSegments.length >= 2) {
                    parentId = pathSegments[pathSegments.length - 2];
                    pageNum = pathSegments[pathSegments.length - 1];
                }

                // Ищем в нашей базе JSON
                if (pageData[parentId] && pageData[parentId][pageNum]) {
                    const dataItem = pageData[parentId][pageNum];
                    realId = dataItem.id;
                    // console.log(`🔗 Нашли ID для текста: ${realId} (Дело: ${parentId}, Стр: ${pageNum})`);

                    // Запрашиваем текст
                    try {
                        const r = await fetch(`/archive/api/markup?id=${realId}`);
                        if (r.ok) {
                            const d = await r.json();
                            if (d.textBlocks) {
                                textContent = d.textBlocks.map(b => b.text).join("\n");
                            } else if (d.pages && d.pages[0] && d.pages[0].textBlocks) {
                                textContent = d.pages[0].textBlocks.map(b => b.text).join("\n");
                            }
                        }
                    } catch (e) {
                        console.error(`Ошибка загрузки текста ${realId}:`, e);
                    }

                    // Небольшая пауза
                    await new Promise(r => setTimeout(r, 200));
                } else {
                    // console.warn(`⚠️ Нет данных в JSON для: ${parentId} / ${pageNum}`);
                }
            }

            results.push({
                title: title, url: href, meta: meta, text: textContent
            });

        } catch (e) {
            console.error(`Ошибка в элементе ${i}:`, e);
        }
    }

    console.log(`✅ Готово к отправке: ${results.length} записей`);
    overlay.innerHTML = `📤 Отправка ${results.length} записей...`;

    // Отправка формы
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = SERVER_URL;
    form.target = '_blank';

    const input = document.createElement('textarea');
    input.name = 'data';
    input.value = JSON.stringify(results);

    form.appendChild(input);
    document.body.appendChild(form);

    form.submit();

    overlay.innerHTML = "✅ Отправлено!";
    setTimeout(() => {
        document.body.removeChild(form);
        overlay.remove();
    }, 5000);
})();
