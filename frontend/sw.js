/* EduSense PWA — кэш оболочки, API не трогаем. */
const CACHE = "edusense-shell-v7";
const PRECACHE = [
  "/",
  "/manifest.json",
  "/assets/edusense-mark-192.png",
  "/assets/edusense-mark-512.png",
  "/assets/edusense-mark-180.png",
  "/assets/edusense-maskable-512.png",
  "/assets/logo.png",
  "/assets/watermark.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/api/")) return;

  // Документы всегда из сети: иначе правки страниц не доезжают до пользователя.
  const isDoc = req.mode === "navigate" || url.pathname.endsWith(".html");
  if (isDoc) {
    event.respondWith(
      fetch(req).catch(() => {
        // Не подсовывать лендинг на /student|/teacher — это даёт бесконечный reload.
        if (url.pathname === "/" || url.pathname === "/index.html") {
          return caches.match("/");
        }
        return new Response(
          "<!doctype html><meta charset='utf-8'><title>EduSense</title><body style='font-family:sans-serif;background:#070b12;color:#e2e8f0;padding:48px;text-align:center'><p>Нет связи с сервером. Обновите страницу.</p><p><a href='/?leave=1' style='color:#7dd3c7'>На главную</a></p></body>",
          { status: 503, headers: { "Content-Type": "text/html; charset=utf-8" } }
        );
      })
    );
    return;
  }

  event.respondWith(
    fetch(req)
      .then((res) => {
        if (res && res.ok && (url.pathname.startsWith("/css/") || url.pathname.startsWith("/js/") || url.pathname.startsWith("/assets/"))) {
          const copy = res.clone();
          caches.open(CACHE).then((cache) => cache.put(req, copy));
        }
        return res;
      })
      .catch(() => caches.match(req).then((hit) => hit || caches.match("/")))
  );
});
