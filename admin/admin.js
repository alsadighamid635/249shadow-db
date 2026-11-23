const message = document.getElementById("message");
const recordsBox = document.getElementById("records");
let refreshTimer = null;

async function login() {
  const password = document.getElementById("adminPassword").value;
  message.textContent = "جارٍ التحقق...";

  try {
    const response = await fetch("/api/admin/login", {
      method: "POST",
      credentials: "same-origin",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({password})
    });

    const result = await response.json();

    if (!response.ok) {
      message.textContent = result.message;
      return;
    }

    document.getElementById("login").hidden = true;
    document.getElementById("dashboard").hidden = false;

    await loadRecords();

    clearInterval(refreshTimer);
    refreshTimer = setInterval(loadRecords, 5000);

  } catch (error) {
    message.textContent = "تعذر الاتصال بالخادم";
  }
}

async function loadRecords() {
  try {
    const response = await fetch("/api/admin/records", {
      credentials: "same-origin"
    });

    if (!response.ok) {
      message.textContent = "انتهت الجلسة أو تعذر تحميل السجلات";
      clearInterval(refreshTimer);
      return;
    }

    const result = await response.json();
    document.getElementById("total").textContent =
      result.records.length;

    recordsBox.replaceChildren();

    result.records.forEach(record => {
      const tr = document.createElement("tr");

      [
        record.id,
        record.username,
        record.demo_value,
        record.created_at
      ].forEach(value => {
        const td = document.createElement("td");
        td.textContent = value;
        tr.appendChild(td);
      });

      const action = document.createElement("td");
      const button = document.createElement("button");
      button.className = "delete";
      button.textContent = "حذف";
      button.onclick = () => deleteRecord(record.id);

      action.appendChild(button);
      tr.appendChild(action);
      recordsBox.appendChild(tr);
    });

    message.textContent = "تم تحديث السجلات بنجاح";

  } catch (error) {
    message.textContent = "تعذر تحميل البيانات";
  }
}

async function deleteRecord(id) {
  if (!confirm("هل تريد حذف هذا السجل؟")) return;

  const response = await fetch(
    "/api/admin/records/" + id,
    {method:"DELETE", credentials:"same-origin"}
  );

  if (response.ok) {
    await loadRecords();
  } else {
    message.textContent = "فشل حذف السجل";
  }
}
