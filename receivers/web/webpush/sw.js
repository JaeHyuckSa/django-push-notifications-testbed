self.addEventListener("push", (event) => {
  const text = event.data ? event.data.text() : "(no data)";
  let title = "Web Push",
    body = text;
  try {
    const data = JSON.parse(text);
    title = data.title || title;
    body = data.body || text;
  } catch (e) {}
  event.waitUntil(
    Promise.all([
      self.registration.showNotification(title, { body }),
      fetch("/received", {
        method: "POST",
        body: JSON.stringify({ source: "webpush", text }),
      }),
      self.clients
        .matchAll({ includeUncontrolled: true })
        .then((cs) => cs.forEach((c) => c.postMessage({ text }))),
    ]),
  );
});
