/* EduSense PWA — кэш оболочки, API не трогаем. */
const CACHE = "edusense-shell-v14";
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

function offlinePage(path) {
  const back = path.startsWith("/teacher")
    ? "/teacher"
    : path.startsWith("/student")
      ? "/student"
      : "/";
  return new Response(
    "<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>" +
      "<title>EduSense</title><body style='font-family:sans-serif;background:#070b12;color:#e2e8f0;padding:40px;text-align:center;line-height:1.5'>" +
      "<p>Нет связи с сервером.</p>" +
      "<p style='opacity:.75;font-size:14px'>Сервер не ответил. Нажмите «Повторить» или очистите данные сайта.</p>" +
      "<p><a href='" +
      back +
      "' style='color:#7dd3c7;margin-right:16px'>Повторить</a>" +
      "<a href='/?leave=1&nosw=1' style='color:#94a3b8'>Сбросить кэш и на главную</a></p></body>",
    { status: 503, headers: { "Content-Type": "text/html; charset=utf-8" } }
  );
}

async function fetchWithRetry(req) {
  try {
    return await fetch(req);
  } catch (_) {
    await new Promise((r) => setTimeout(r, 600));
    return fetch(req);
  }
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/api/")) return;

  const isDoc = req.mode === "navigate" || url.pathname.endsWith(".html");
  if (isDoc) {
    event.respondWith(
      fetchWithRetry(req).catch(() => {
        if (url.pathname === "/" || url.pathname === "/index.html") {
          return caches.match("/").then((hit) => hit || offlinePage("/"));
        }
        return offlinePage(url.pathname);
      })
    );
    return;
  }

  event.respondWith(
    fetch(req)
      .then((res) => {
        if (
          res &&
          res.ok &&
          (url.pathname.startsWith("/css/") ||
            url.pathname.startsWith("/js/") ||
            url.pathname.startsWith("/assets/"))
        ) {
          const copy = res.clone();
          caches.open(CACHE).then((cache) => cache.put(req, copy));
        }
        return res;
      })
      .catch(() => caches.match(req).then((hit) => hit || caches.match("/")))
  );
});
