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

async function handleSearchClick() {
  const issues = getSelectedIssues();

  if (issues.length === 0) {
    console.warn("Select at least one issue before searching.");
    return;
  }

  try {
    const data = await searchCases(issues);
    if (data.results.length === 0) {
      console.log("No matching orders found.");
    } else {
      console.log("Search results:", data.results);
    }
  } catch (error) {
    console.error(error);
  }
}

document.getElementById("search-button").addEventListener("click", handleSearchClick);
