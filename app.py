from flask import Flask, render_template_string, request, jsonify
from curl_cffi import requests as cffi_requests
import os

app = Flask(__name__)
session = cffi_requests.Session(impersonate="chrome120")
session.headers.update({
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.vinted.it/"
})

def init_vinted_session():
    try:
        session.get("https://www.vinted.it", timeout=10)
    except Exception as e:
        print(f"Errore cookie: {e}")

init_vinted_session()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="it" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Vinted Sniper Render</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0b0f19; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    </style>
</head>
<body class="min-h-screen p-3 pb-20">

    <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4 mb-4 shadow-xl sticky top-2 z-50">
        <div class="flex justify-between items-center mb-3">
            <div class="flex items-center gap-2">
                <span class="text-xl">⚡</span>
                <h1 class="text-sm font-bold text-lime-400 tracking-wide">SNIPER RENDER</h1>
            </div>
            <span class="text-xs bg-slate-800 px-2.5 py-1 rounded-full border border-slate-700">
                Trovati: <strong id="counter" class="text-lime-400">0</strong>
            </span>
        </div>

        <div class="grid grid-cols-3 gap-2 mb-3">
            <input id="searchText" type="text" value="nike basket" placeholder="Cosa cerchi?" 
                   class="col-span-2 bg-slate-950 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-white">
            <input id="priceTo" type="number" value="15" placeholder="Max €" 
                   class="bg-slate-950 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-white">
        </div>

        <div class="flex gap-2">
            <button id="toggleBtn" onclick="toggleMonitor()" 
                    class="flex-1 bg-lime-400 text-slate-950 font-extrabold py-2.5 rounded-xl text-sm shadow">
                ▶ Avvia Radar (5s)
            </button>
            <button onclick="clearFeed()" 
                    class="bg-slate-800 text-slate-200 px-4 py-2.5 rounded-xl text-sm border border-slate-700">
                🗑
            </button>
        </div>
        <div id="statusText" class="text-[11px] text-slate-400 mt-2 text-center">Pronto — Premi Avvia Radar</div>
    </div>

    <div id="itemsGrid" class="grid grid-cols-2 gap-3"></div>

    <script>
        let isRunning = false;
        let intervalId = null;
        let seenIds = new Set();

        function toggleMonitor() {
            const btn = document.getElementById('toggleBtn');
            const statusText = document.getElementById('statusText');

            if (!isRunning) {
                isRunning = true;
                btn.innerHTML = "⏸ Ferma Radar";
                btn.className = "flex-1 bg-rose-600 text-white font-extrabold py-2.5 rounded-xl text-sm shadow";
                statusText.innerText = "🟢 RADAR ATTIVO — Scansione ogni 5 secondi...";
                fetchItems();
                intervalId = setInterval(fetchItems, 5000);
            } else {
                isRunning = false;
                clearInterval(intervalId);
                btn.innerHTML = "▶ Avvia Radar (5s)";
                btn.className = "flex-1 bg-lime-400 text-slate-950 font-extrabold py-2.5 rounded-xl text-sm shadow";
                statusText.innerText = "In pausa";
            }
        }

        function clearFeed() {
            document.getElementById('itemsGrid').innerHTML = '';
            seenIds.clear();
            document.getElementById('counter').innerText = '0';
        }

        async function fetchItems() {
            const search = document.getElementById('searchText').value;
            const priceTo = document.getElementById('priceTo').value;
            const statusText = document.getElementById('statusText');

            try {
                const res = await fetch(`/api/vinted/items?search=${encodeURIComponent(search)}&price_to=${encodeURIComponent(priceTo)}`);
                const data = await res.json();

                if (data.error) {
                    statusText.innerText = "⚠️ " + data.error;
                    return;
                }

                if (data.items && data.items.length > 0) {
                    statusText.innerText = "🟢 Radar attivo — Aggiornato ora";
                    const grid = document.getElementById('itemsGrid');
                    data.items.reverse().forEach(item => {
                        if (!seenIds.has(item.id)) {
                            seenIds.add(item.id);
                            const card = document.createElement('div');
                            card.className = "bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg flex flex-col justify-between";
                            card.innerHTML = `
                                <div>
                                    <div class="relative h-44 w-full bg-slate-950">
                                        <img src="${item.photo_url}" class="w-full h-full object-cover">
                                        <span class="absolute top-2 left-2 bg-lime-400 text-slate-950 text-xs font-extrabold px-2 py-0.5 rounded-md shadow">
                                            ${item.price} €
                                        </span>
                                        <span class="absolute bottom-2 right-2 bg-slate-900/90 text-white text-[10px] font-bold px-2 py-0.5 rounded border border-slate-700">
                                            📏 ${item.size_title || 'N/A'}
                                        </span>
                                    </div>
                                    <div class="p-2.5">
                                        <div class="text-[10px] font-bold text-lime-400 uppercase truncate">${item.brand_title || 'Vinted'}</div>
                                        <h3 class="text-xs font-medium text-white truncate">${item.title}</h3>
                                        <p class="text-[10px] text-slate-400">Incl. tasse: ${item.total_price}€</p>
                                    </div>
                                </div>
                                <div class="p-2 pt-0 flex gap-1.5">
                                    <a href="${item.url}" target="_blank" 
                                       class="flex-1 bg-lime-400 text-center text-slate-950 text-[11px] font-extrabold py-2 rounded-lg">
                                        ⚡ Apri
                                    </a>
                                    <a href="${item.photo_url}" target="_blank"
                                       class="bg-slate-800 text-white text-[11px] px-2.5 py-2 rounded-lg border border-slate-700">
                                        🖼
                                    </a>
                                </div>
                            `;
                            grid.prepend(card);
                        }
                    });
                    document.getElementById('counter').innerText = seenIds.size;
                } else {
                    statusText.innerText = "🟢 Radar attivo — Nessun nuovo oggetto trovato";
                }
            } catch (err) {
                console.error(err);
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/vinted/items")
def api_scan():
    search_text = request.args.get("search", "nike")
    price_to = request.args.get("price_to", "15")
    params = {
        "page": 1, "per_page": 20,
        "search_text": search_text, "price_to": price_to,
        "currency": "EUR", "order": "newest_first"
    }
    try:
        res = session.get("https://www.vinted.it/api/v2/catalog/items", params=params, timeout=10)
        if res.status_code in [401, 403, 404]:
            init_vinted_session()
            res = session.get("https://www.vinted.it/api/v2/catalog/items", params=params, timeout=10)
        
        if res.status_code == 200:
            raw_items = res.json().get("items", [])
            clean_items = []
            for item in raw_items:
                photo_info = item.get("photo") or {}
                photo_url = photo_info.get("full_size_url") or photo_info.get("url") or ""
                clean_items.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "brand_title": item.get("brand_title"),
                    "size_title": item.get("size_title"),
                    "price": item.get("price", {}).get("amount", "N/A"),
                    "total_price": item.get("total_item_price", {}).get("amount", "N/A"),
                    "url": item.get("url"),
                    "photo_url": photo_url
                })
            return jsonify({"items": clean_items})
        return jsonify({"items": [], "error": f"Blocco HTTP {res.status_code}"})
    except Exception as e:
        return jsonify({"items": [], "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
