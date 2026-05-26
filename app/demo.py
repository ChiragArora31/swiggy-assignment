DEMO_HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Project Management Demo</title>
  <style>
    :root {
      --bg: #f6f7f9;
      --panel: #ffffff;
      --ink: #18202f;
      --muted: #667085;
      --line: #d9dee8;
      --brand: #176b87;
      --brand-dark: #0d4d63;
      --green: #227a4a;
      --amber: #a45f0b;
      --red: #b42318;
      --blue-soft: #e8f4f8;
      --green-soft: #e9f7ef;
      --amber-soft: #fff3df;
      --red-soft: #fdecec;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }
    button, input, select, textarea { font: inherit; }
    button {
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--ink);
      border-radius: 6px;
      min-height: 34px;
      padding: 7px 10px;
      cursor: pointer;
    }
    button.primary { background: var(--brand); border-color: var(--brand); color: #fff; }
    button.primary:hover { background: var(--brand-dark); }
    button.danger { color: var(--red); border-color: #f0b8b3; background: var(--red-soft); }
    input, select, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      padding: 8px 9px;
      min-height: 36px;
    }
    textarea { min-height: 76px; resize: vertical; }
    .shell { min-height: 100vh; display: grid; grid-template-rows: auto 1fr; }
    .topbar {
      background: #111827;
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 18px;
      gap: 14px;
      border-bottom: 1px solid #2d3648;
    }
    .title { display: flex; align-items: baseline; gap: 10px; min-width: 240px; }
    .title h1 { margin: 0; font-size: 18px; line-height: 1.2; font-weight: 720; }
    .title span { color: #b8c1d1; font-size: 13px; }
    .top-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
    .top-actions select { width: 190px; background: #1f2937; color: #fff; border-color: #3c4657; }
    .top-actions a { color: #d5eaf2; font-size: 13px; text-decoration: none; }
    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 390px;
      gap: 14px;
      padding: 14px;
      align-items: start;
    }
    .main { display: grid; gap: 14px; min-width: 0; }
    .toolbar {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      display: grid;
      grid-template-columns: 1.2fr repeat(4, minmax(110px, .7fr)) auto;
      gap: 10px;
      align-items: end;
    }
    label { display: grid; gap: 5px; font-size: 12px; color: var(--muted); font-weight: 650; }
    .board {
      display: grid;
      grid-template-columns: repeat(4, minmax(220px, 1fr));
      gap: 12px;
      min-height: 480px;
    }
    .column {
      background: #eef1f5;
      border: 1px solid var(--line);
      border-radius: 8px;
      min-width: 0;
      display: grid;
      grid-template-rows: auto 1fr;
    }
    .column-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 11px;
      border-bottom: 1px solid var(--line);
      color: #344054;
      font-size: 13px;
      font-weight: 760;
    }
    .count { color: var(--muted); font-weight: 680; }
    .cards { padding: 9px; display: grid; gap: 8px; align-content: start; }
    .issue {
      border: 1px solid #d7dce5;
      background: #fff;
      border-radius: 8px;
      padding: 10px;
      display: grid;
      gap: 8px;
      cursor: pointer;
    }
    .issue.selected { border-color: var(--brand); box-shadow: 0 0 0 2px rgba(23, 107, 135, .14); }
    .issue-top { display: flex; justify-content: space-between; gap: 8px; align-items: center; }
    .key { font-weight: 780; color: var(--brand-dark); font-size: 12px; }
    .pill { font-size: 11px; padding: 3px 7px; border-radius: 999px; border: 1px solid var(--line); color: #344054; background: #f7f8fb; white-space: nowrap; }
    .pill.high, .pill.critical { color: var(--red); background: var(--red-soft); border-color: #f6c6c1; }
    .pill.medium { color: var(--amber); background: var(--amber-soft); border-color: #f2d3a8; }
    .pill.done { color: var(--green); background: var(--green-soft); border-color: #b9e3ca; }
    .issue-title { font-size: 14px; line-height: 1.35; font-weight: 680; }
    .meta { display: flex; gap: 7px; flex-wrap: wrap; color: var(--muted); font-size: 12px; }
    .side { display: grid; gap: 14px; min-width: 0; }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      min-width: 0;
    }
    .panel-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 11px 12px;
      border-bottom: 1px solid var(--line);
      background: #fbfcfe;
    }
    .panel-head h2 { margin: 0; font-size: 14px; }
    .panel-body { padding: 12px; display: grid; gap: 10px; }
    .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; }
    .row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    .detail-title { font-size: 16px; font-weight: 760; margin: 0; line-height: 1.3; }
    .description { color: var(--muted); font-size: 13px; line-height: 1.45; margin: 0; }
    .log {
      max-height: 220px;
      overflow: auto;
      display: grid;
      gap: 7px;
    }
    .log-item {
      border-left: 3px solid var(--brand);
      background: var(--blue-soft);
      padding: 7px 8px;
      font-size: 12px;
      color: #344054;
      border-radius: 0 6px 6px 0;
      word-break: break-word;
    }
    .toast {
      position: fixed;
      right: 16px;
      bottom: 16px;
      background: #111827;
      color: #fff;
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 13px;
      max-width: 420px;
      opacity: 0;
      transform: translateY(10px);
      pointer-events: none;
      transition: .18s ease;
      z-index: 4;
    }
    .toast.show { opacity: 1; transform: translateY(0); }
    .empty { color: var(--muted); font-size: 13px; padding: 8px 0; }
    @media (max-width: 1120px) {
      .layout { grid-template-columns: 1fr; }
      .side { grid-template-columns: 1fr 1fr; }
      .toolbar { grid-template-columns: 1fr 1fr 1fr; }
    }
    @media (max-width: 760px) {
      .topbar { align-items: flex-start; flex-direction: column; }
      .layout { padding: 10px; }
      .board { grid-template-columns: 1fr; min-height: auto; }
      .side { grid-template-columns: 1fr; }
      .toolbar { grid-template-columns: 1fr; }
      .grid2 { grid-template-columns: 1fr; }
      .top-actions select { width: 100%; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <header class="topbar">
      <div class="title">
        <h1>Project Management Platform</h1>
        <span id="projectName">PROJ board</span>
      </div>
      <div class="top-actions">
        <select id="userSelect" title="Current demo user"></select>
        <button id="refreshBtn">Refresh</button>
        <a href="/docs" target="_blank">Swagger</a>
        <a href="/health" target="_blank">Health</a>
      </div>
    </header>

    <main class="layout">
      <section class="main">
        <div class="toolbar">
          <label>Search
            <input id="searchInput" placeholder="title, description, comment" />
          </label>
          <label>Priority
            <select id="priorityFilter">
              <option value="">Any</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </label>
          <label>Type
            <select id="typeFilter">
              <option value="">Any</option>
              <option value="epic">Epic</option>
              <option value="story">Story</option>
              <option value="task">Task</option>
              <option value="bug">Bug</option>
              <option value="sub_task">Sub-task</option>
            </select>
          </label>
          <label>Assignee
            <select id="assigneeFilter"><option value="">Any</option></select>
          </label>
          <label>Sprint
            <select id="sprintFilter"><option value="">Any</option></select>
          </label>
          <button id="searchBtn" class="primary">Search</button>
        </div>
        <div id="board" class="board"></div>
      </section>

      <aside class="side">
        <section class="panel">
          <div class="panel-head">
            <h2>Selected Issue</h2>
            <button id="watchBtn">Watch</button>
          </div>
          <div class="panel-body" id="issueDetail">
            <div class="empty">Select an issue from the board.</div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head"><h2>Create Issue</h2></div>
          <div class="panel-body">
            <div class="grid2">
              <label>Type
                <select id="newType">
                  <option value="story">Story</option>
                  <option value="task">Task</option>
                  <option value="bug">Bug</option>
                  <option value="epic">Epic</option>
                </select>
              </label>
              <label>Priority
                <select id="newPriority">
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="critical">Critical</option>
                  <option value="low">Low</option>
                </select>
              </label>
            </div>
            <label>Title
              <input id="newTitle" value="Demo API review flow" />
            </label>
            <label>Description
              <textarea id="newDescription">Created from the live demo UI.</textarea>
            </label>
            <div class="grid2">
              <label>Assignee
                <select id="newAssignee"></select>
              </label>
              <label>Points
                <input id="newPoints" type="number" min="0" value="3" />
              </label>
            </div>
            <button id="createBtn" class="primary">Create</button>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head"><h2>Sprint</h2></div>
          <div class="panel-body">
            <label>Active sprint
              <select id="completeSprint"></select>
            </label>
            <label>Carry over to
              <select id="carrySprint"></select>
            </label>
            <button id="completeBtn">Complete sprint</button>
            <div id="sprintResult" class="empty"></div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head"><h2>Activity</h2></div>
          <div class="panel-body">
            <div id="activityLog" class="log"></div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head"><h2>Notifications</h2></div>
          <div class="panel-body">
            <div id="notifications" class="log"></div>
          </div>
        </section>
      </aside>
    </main>
  </div>
  <div id="toast" class="toast"></div>

  <script>
    const state = {
      projectId: 1,
      users: [],
      sprints: [],
      board: null,
      selected: null,
      searchResults: null,
      lastEventId: null,
      ws: null
    };

    const $ = (id) => document.getElementById(id);
    const headers = () => ({ "Content-Type": "application/json", "X-User-Id": $("userSelect").value || "1" });
    const userName = (id) => state.users.find(u => u.id === id)?.display_name || (id ? `User ${id}` : "Unassigned");

    function toast(message) {
      const el = $("toast");
      el.textContent = message;
      el.classList.add("show");
      clearTimeout(window.__toastTimer);
      window.__toastTimer = setTimeout(() => el.classList.remove("show"), 2800);
    }

    async function api(path, options = {}) {
      const response = await fetch(path, { ...options, headers: { ...headers(), ...(options.headers || {}) } });
      if (!response.ok) {
        let detail;
        try { detail = await response.json(); } catch { detail = { detail: response.statusText }; }
        throw new Error(JSON.stringify(detail.detail || detail));
      }
      if (response.status === 204) return null;
      return response.json();
    }

    function issueCard(issue) {
      const done = issue.status.is_done ? " done" : "";
      return `
        <article class="issue ${state.selected?.id === issue.id ? "selected" : ""}" data-id="${issue.id}">
          <div class="issue-top">
            <span class="key">${issue.issue_key}</span>
            <span class="pill ${issue.priority}">${issue.priority}</span>
          </div>
          <div class="issue-title">${escapeHtml(issue.title)}</div>
          <div class="meta">
            <span>${issue.issue_type}</span>
            <span class="pill${done}">${issue.status.name}</span>
            <span>${issue.story_points ?? 0} pts</span>
            <span>${userName(issue.assignee?.id)}</span>
          </div>
        </article>
      `;
    }

    function renderBoard() {
      const board = $("board");
      const searchRows = state.searchResults;
      if (searchRows) {
        board.innerHTML = `
          <section class="column" style="grid-column: 1 / -1">
            <div class="column-head"><span>Search Results</span><span class="count">${searchRows.length}</span></div>
            <div class="cards">${searchRows.map(issueCard).join("") || `<div class="empty">No matching issues.</div>`}</div>
          </section>
        `;
      } else if (state.board) {
        board.innerHTML = state.board.columns.map(col => `
          <section class="column">
            <div class="column-head"><span>${col.status.name}</span><span class="count">${col.issues.length}</span></div>
            <div class="cards">${col.issues.map(issueCard).join("") || `<div class="empty">No issues.</div>`}</div>
          </section>
        `).join("");
      }
      document.querySelectorAll(".issue").forEach(card => {
        card.addEventListener("click", () => selectIssue(Number(card.dataset.id)));
      });
    }

    function renderDetail() {
      const box = $("issueDetail");
      const issue = state.selected;
      if (!issue) {
        box.innerHTML = `<div class="empty">Select an issue from the board.</div>`;
        return;
      }
      const statusOptions = (state.board?.columns || []).map(col => `<option value="${col.status.name}">${col.status.name}</option>`).join("");
      box.innerHTML = `
        <p class="detail-title">${issue.issue_key}: ${escapeHtml(issue.title)}</p>
        <p class="description">${escapeHtml(issue.description || "No description")}</p>
        <div class="grid2">
          <label>Status
            <select id="targetStatus">${statusOptions}</select>
          </label>
          <label>Version
            <input id="expectedVersion" type="number" value="${issue.version}" />
          </label>
        </div>
        <div class="row">
          <button id="transitionBtn" class="primary">Transition</button>
          <button id="invalidBtn" class="danger">Try invalid Done</button>
          <button id="staleBtn">Stale patch</button>
        </div>
        <label>Comment
          <textarea id="commentBody">@bob please review ${issue.issue_key}.</textarea>
        </label>
        <button id="commentBtn">Add comment</button>
        <div class="meta">
          <span>Assignee: ${userName(issue.assignee?.id)}</span>
          <span>Reporter: ${userName(issue.reporter?.id)}</span>
          <span>Sprint: ${issue.sprint_id || "Backlog"}</span>
        </div>
      `;
      $("targetStatus").value = issue.status.name;
      $("transitionBtn").onclick = transitionSelected;
      $("invalidBtn").onclick = invalidTransition;
      $("staleBtn").onclick = stalePatch;
      $("commentBtn").onclick = addComment;
    }

    function renderActivity(items = []) {
      $("activityLog").innerHTML = items.map(item => {
        state.lastEventId = Math.max(state.lastEventId || 0, item.id);
        return `<div class="log-item">${item.id} ${item.event_type}: ${escapeHtml(JSON.stringify(item.payload))}</div>`;
      }).join("") || `<div class="empty">No activity yet.</div>`;
    }

    function renderNotifications(items = []) {
      $("notifications").innerHTML = items.map(item => `<div class="log-item">${escapeHtml(item.type)}: ${escapeHtml(item.message)}</div>`).join("") || `<div class="empty">No notifications for this user.</div>`;
    }

    function fillSelect(select, rows, formatter, blank) {
      const current = select.value;
      select.innerHTML = (blank ? `<option value="">${blank}</option>` : "") + rows.map(formatter).join("");
      if ([...select.options].some(o => o.value === current)) select.value = current;
    }

    async function loadBasics() {
      state.users = await api("/api/users");
      state.sprints = await api("/api/projects/1/sprints");
      fillSelect($("userSelect"), state.users, u => `<option value="${u.id}">${u.display_name}</option>`);
      fillSelect($("newAssignee"), state.users, u => `<option value="${u.id}">${u.display_name}</option>`);
      fillSelect($("assigneeFilter"), state.users, u => `<option value="${u.id}">${u.display_name}</option>`, "Any");
      fillSelect($("sprintFilter"), state.sprints, s => `<option value="${s.id}">${s.name}</option>`, "Any");
      fillSelect($("completeSprint"), state.sprints.filter(s => s.state === "active"), s => `<option value="${s.id}">${s.name}</option>`);
      fillSelect($("carrySprint"), state.sprints.filter(s => s.state !== "completed"), s => `<option value="${s.id}">${s.name}</option>`);
    }

    async function loadBoard() {
      state.board = await api("/api/projects/1/board");
      state.searchResults = null;
      renderBoard();
      if (state.selected) {
        try { state.selected = await api(`/api/issues/${state.selected.id}`); } catch { state.selected = null; }
        renderDetail();
      }
    }

    async function loadActivity() {
      const data = await api("/api/projects/1/activity?limit=12");
      renderActivity(data.items || []);
    }

    async function loadNotifications() {
      renderNotifications(await api("/api/notifications"));
    }

    async function refreshAll() {
      await loadBasics();
      await loadBoard();
      await loadActivity();
      await loadNotifications();
    }

    async function selectIssue(id) {
      state.selected = await api(`/api/issues/${id}`);
      renderBoard();
      renderDetail();
    }

    async function createIssue() {
      const payload = {
        issue_type: $("newType").value,
        title: $("newTitle").value,
        description: $("newDescription").value,
        priority: $("newPriority").value,
        assignee_id: Number($("newAssignee").value),
        story_points: Number($("newPoints").value || 0),
        labels: ["demo"]
      };
      const issue = await api("/api/projects/1/issues", { method: "POST", body: JSON.stringify(payload) });
      state.selected = issue;
      toast(`Created ${issue.issue_key}`);
      await refreshAll();
    }

    async function transitionSelected() {
      if (!state.selected) return;
      const issue = await api(`/api/issues/${state.selected.id}/transitions`, {
        method: "POST",
        body: JSON.stringify({
          target_status_name: $("targetStatus").value,
          expected_version: Number($("expectedVersion").value)
        })
      });
      state.selected = issue;
      toast(`${issue.issue_key} moved to ${issue.status.name}`);
      await refreshAll();
    }

    async function invalidTransition() {
      if (!state.selected) return;
      try {
        await api(`/api/issues/${state.selected.id}/transitions`, {
          method: "POST",
          body: JSON.stringify({ target_status_name: "Done", expected_version: state.selected.version })
        });
      } catch (error) {
        toast(`422 validation: ${error.message.slice(0, 180)}`);
      }
    }

    async function stalePatch() {
      if (!state.selected) return;
      await api(`/api/issues/${state.selected.id}`, {
        method: "PATCH",
        body: JSON.stringify({ expected_version: state.selected.version, priority: "critical" })
      });
      try {
        await api(`/api/issues/${state.selected.id}`, {
          method: "PATCH",
          body: JSON.stringify({ expected_version: state.selected.version, title: `${state.selected.title} stale` })
        });
      } catch (error) {
        toast(`409 conflict: ${error.message.slice(0, 180)}`);
      }
      await refreshAll();
    }

    async function addComment() {
      if (!state.selected) return;
      const comment = await api(`/api/issues/${state.selected.id}/comments`, {
        method: "POST",
        body: JSON.stringify({ body: $("commentBody").value })
      });
      toast(`Comment ${comment.id} added`);
      await refreshAll();
    }

    async function watchSelected() {
      if (!state.selected) return;
      await api(`/api/issues/${state.selected.id}/watch`, { method: "POST" });
      toast(`Watching ${state.selected.issue_key}`);
      await loadActivity();
    }

    async function searchIssues() {
      const params = new URLSearchParams({ project_id: "1", limit: "50" });
      if ($("searchInput").value) params.set("q", $("searchInput").value);
      if ($("priorityFilter").value) params.set("priority", $("priorityFilter").value);
      if ($("typeFilter").value) params.set("issue_type", $("typeFilter").value);
      if ($("assigneeFilter").value) params.set("assignee_id", $("assigneeFilter").value);
      if ($("sprintFilter").value) params.set("sprint_id", $("sprintFilter").value);
      const data = await api(`/api/search?${params}`);
      state.searchResults = data.items || [];
      renderBoard();
    }

    async function completeSprint() {
      const sprintId = Number($("completeSprint").value);
      const targetId = Number($("carrySprint").value);
      if (!sprintId || !targetId) return;
      const activeIssues = state.board.columns.flatMap(c => c.issues).filter(i => i.sprint_id === sprintId && !i.status.is_done);
      const carryIds = activeIssues.slice(0, 2).map(i => i.id);
      const result = await api(`/api/sprints/${sprintId}/complete`, {
        method: "POST",
        body: JSON.stringify({ carry_over_issue_ids: carryIds, new_sprint_id: targetId })
      });
      $("sprintResult").textContent = `Velocity ${result.velocity}. Incomplete ${result.incomplete_issue_ids.length}. Carried ${result.carried_over_issue_ids.length}.`;
      toast("Sprint completed");
      await refreshAll();
    }

    function connectSocket() {
      if (!("WebSocket" in window)) return;
      const protocol = location.protocol === "https:" ? "wss" : "ws";
      const url = `${protocol}://${location.host}/ws/projects/1/board?user_id=${$("userSelect").value || 1}${state.lastEventId ? `&last_event_id=${state.lastEventId}` : ""}`;
      try {
        state.ws = new WebSocket(url);
        state.ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.event_id) state.lastEventId = data.event_id;
          loadActivity();
          if (["issue_created", "issue_updated", "issue_moved", "sprint_updated", "comment_added"].includes(data.event_type)) {
            loadBoard();
          }
        };
      } catch {
        state.ws = null;
      }
    }

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    $("refreshBtn").onclick = refreshAll;
    $("createBtn").onclick = createIssue;
    $("watchBtn").onclick = watchSelected;
    $("searchBtn").onclick = searchIssues;
    $("completeBtn").onclick = completeSprint;
    $("userSelect").onchange = () => { loadNotifications(); connectSocket(); };

    refreshAll()
      .then(connectSocket)
      .catch(error => toast(error.message));
  </script>
</body>
</html>
"""
