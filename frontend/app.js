const form = document.getElementById("demoForm");
const message = document.getElementById("message");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const data = Object.fromEntries(new FormData(form));

  const response = await fetch("/api/demo-records", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(data)
  });

  const result = await response.json();
  message.textContent = result.message;
  if (response.ok) form.reset();
});
