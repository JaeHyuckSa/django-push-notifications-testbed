// the Firebase config comes in the registration URL, see index.html
importScripts(
  "https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js",
);
importScripts(
  "https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging-compat.js",
);
firebase.initializeApp(Object.fromEntries(new URL(location).searchParams));
firebase.messaging().onBackgroundMessage((payload) => {
  const data = payload.data || {};
  fetch("/received", {
    method: "POST",
    body: JSON.stringify({ source: "fcm", where: "background", data }),
  });
  self.clients
    .matchAll({ type: "window", includeUncontrolled: true })
    .then((clients) => clients.forEach((c) => c.postMessage({ fcm: payload })));
});
