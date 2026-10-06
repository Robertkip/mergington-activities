const listEl = document.getElementById("activities-list");
const messageEl = document.getElementById("message");

function showMessage(text, isError) {
  messageEl.textContent = text;
  messageEl.className = isError ? "message error" : "message success";
}

// The page is built with textContent, never innerHTML, so an email typed by a
// student can never inject markup into the page.
function renderActivity(name, activity) {
  const card = document.createElement("article");
  card.className = "activity";

  const title = document.createElement("h2");
  title.textContent = name;

  const description = document.createElement("p");
  description.textContent = activity.description;

  const schedule = document.createElement("p");
  schedule.className = "schedule";
  schedule.textContent = activity.schedule;

  const participantsTitle = document.createElement("h3");
  participantsTitle.textContent = "Signed up";

  const participants = document.createElement("ul");
  for (const email of activity.participants) {
    const item = document.createElement("li");
    item.textContent = email;
    participants.appendChild(item);
  }

  const form = document.createElement("form");
  const input = document.createElement("input");
  input.type = "email";
  input.required = true;
  input.placeholder = "your.email@mergington.edu";
  input.setAttribute("aria-label", "Email address for " + name);
  const button = document.createElement("button");
  button.type = "submit";
  button.textContent = "Sign up";
  form.append(input, button);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    signUp(name, input.value);
  });

  card.append(title, description, schedule, participantsTitle, participants, form);
  return card;
}

async function loadActivities() {
  const response = await fetch("/activities");
  const activities = await response.json();
  listEl.replaceChildren(
    ...Object.entries(activities).map(([name, activity]) => renderActivity(name, activity))
  );
}

async function signUp(name, email) {
  const url = "/activities/" + encodeURIComponent(name) + "/signup?email=" + encodeURIComponent(email);
  const response = await fetch(url, { method: "POST" });
  const result = await response.json();
  if (response.ok) {
    showMessage(result.message, false);
    await loadActivities();
  } else {
    showMessage(typeof result.detail === "string" ? result.detail : "Something went wrong.", true);
  }
}

loadActivities().catch(() => showMessage("Could not load activities. Please try again.", true));
