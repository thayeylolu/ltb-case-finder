const API_BASE_URL = "http://127.0.0.1:8000";

function getSelectedIssues() {
  const checkboxes = document.querySelectorAll('input[name="issues"]:checked');
  return Array.from(checkboxes).map((checkbox) => checkbox.value);
}

async function searchCases(issues) {
  const response = await fetch(`${API_BASE_URL}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ issues }),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    throw new Error(`Search request failed (${response.status}): ${JSON.stringify(errorBody)}`);
  }

  return response.json();
}

const RESULT_COLUMNS = ["File Number", "Order Date", "Issues", "City", "Document Type", "View Order"];

function renderResults(results) {
  const container = document.getElementById("results");
  container.innerHTML = "";

  if (results.length === 0) {
    return;
  }

  const table = document.createElement("table");

  const headerRow = document.createElement("tr");
  RESULT_COLUMNS.forEach((label) => {
    const th = document.createElement("th");
    th.textContent = label;
    headerRow.appendChild(th);
  });
  const thead = document.createElement("thead");
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  results.forEach((result) => {
    const row = document.createElement("tr");

    const fileNumberCell = document.createElement("td");
    fileNumberCell.textContent = result.file_number;
    row.appendChild(fileNumberCell);

    const orderDateCell = document.createElement("td");
    orderDateCell.textContent = result.order_date;
    row.appendChild(orderDateCell);

    const issuesCell = document.createElement("td");
    issuesCell.className = "issues-cell";
    issuesCell.textContent = result.issues.join(" · ");
    row.appendChild(issuesCell);

    [result.city || "", result.document_type].forEach((text) => {
      const td = document.createElement("td");
      td.textContent = text;
      row.appendChild(td);
    });

    const viewOrderCell = document.createElement("td");
    const link = document.createElement("a");
    link.href = result.view_order_url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = "View Order";
    viewOrderCell.appendChild(link);
    row.appendChild(viewOrderCell);

    tbody.appendChild(row);
  });
  table.appendChild(tbody);

  container.appendChild(table);
}

async function handleSearchClick() {
  const issues = getSelectedIssues();

  if (issues.length === 0) {
    console.warn("Select at least one issue before searching.");
    return;
  }

  try {
    const data = await searchCases(issues);
    renderResults(data.results);
  } catch (error) {
    console.error(error);
  }
}

document.getElementById("search-button").addEventListener("click", handleSearchClick);
