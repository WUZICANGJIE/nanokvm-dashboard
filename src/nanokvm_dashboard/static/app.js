"use strict";

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const translations = {
  zh: {
    dashboard: "设备面板", favorites: "收藏", settingsShort: "设置", heading: "我的设备",
    deviceCount: "台设备", onlineCount: "台在线", addressHeading: "地址 / 主机名 / MAC", status: "状态", response: "响应", actions: "操作", filters: "设备筛选",
    addDevice: "添加设备", totalDevices: "设备总数", savedDevices: "已保存的控制台", online: "在线", offline: "离线",
    unknown: "待检查", unavailable: "待检查 / 离线", webReachable: "管理页面可达", keepRecords: "设备记录会继续保留",
    discoveryTitle: "每 {seconds} 秒自动扫描", scan: "扫描设备", scanning: "扫描中…",
    scanProgress: "正在查找并确认设备…", disabled: "自动发现已关闭", disabledHint: "可手动添加设备。",
    all: "全部", emptyTitle: "还没有设备", emptyHint: "打开 NanoKVM 的 mDNS，然后扫描设备。也可以手动添加地址。",
    manualAdd: "手动添加第一台设备", noResults: "没有符合条件的设备", noResultsHint: "试试其他搜索词，或切换设备筛选。",
    statusNote: "在线状态仅代表 Web 页面可达，不代表受控电脑电源或 HDMI 状态。", openConsole: "打开控制台", name: "设备名称",
    url: "访问地址", urlHelp: "支持局域网 IP 或域名，以及 NanoKVM 的自签名 HTTPS。", notes: "备注", favoriteDevice: "收藏这台设备",
    removeDevice: "移除设备", cancel: "取消", save: "保存设备", saving: "保存中…", settings: "面板设置", appearance: "外观",
    appearanceHint: "选择适合你工作空间的主题。", lightTheme: "切换浅色", darkTheme: "切换深色", backup: "设备备份",
    backupHint: "导出名称、访问地址、备注和收藏；导入会合并现有记录。", export: "导出 JSON", import: "导入 JSON",
    discoverySettings: "自动发现", restoreDiscovery: "重新发现已移除的设备", noDevices: "扫描不到设备？",
    discoveryHelp: "在 NanoKVM 的 Settings → Device 中开启 mDNS。Unraid 容器使用 Host 网络；如果有多个网卡，可通过 MDNS_INTERFACES 指定 LAN 的 IPv4 地址。",
    identityHelp: "同一 mDNS 主机名的有线与无线地址会合并。两台不同设备请设置不同的主机名。",
    privacy: "面板只读取设备网页来检查状态，不保存 NanoKVM 密码，也不操作电源或键鼠。", confirmRemove: "确认移除",
    editDevice: "编辑设备", copy: "复制地址", copied: "地址已复制", saved: "设备已保存", removed: "设备已移除", restored: "已清除发现忽略列表",
    imported: "设备配置已导入", importError: "无法导入，请选择有效的设备 JSON 备份。", fileLarge: "备份文件不能超过 1 MB。",
    manual: "手动添加", discovered: "mDNS 发现", noNotes: "还没有备注", lastSeen: "上次在线", neverSeen: "尚未完成在线检查",
    refresh: "刷新状态", connectionError: "无法连接面板后端。显示的是上次结果，请检查容器是否运行。", requestError: "请求失败",
    search: "搜索名称、地址、MAC 或备注", notesPlaceholder: "这台 KVM 连接了哪台电脑？", namePlaceholder: "例如 kvm-server",
    macHint: "最近获取的 mDNS 广播 MAC；多个地址不对应特定 IP 或有线 / Wi-Fi 接口。",
    macMissingHint: "尚未从设备的 mDNS 广播中获取 MAC 地址。",
    removePrompt: "确定移除这台设备吗？自动发现的设备会被暂时忽略，可在设置中恢复。", neverScanned: "等待首次扫描。",
    scanned: "上次扫描", candidateLabel: "个服务主机", verifiedLabel: "台 NanoKVM", interval: "自动扫描间隔", seconds: "秒",
    interfaces: "监听网卡", allInterfaces: "所有可用网卡", addresses: "已发现地址", scanFailed: "扫描失败", justNow: "刚刚",
  },
  en: {
    dashboard: "Dashboard", favorites: "Favorites", settingsShort: "Settings", heading: "My devices",
    deviceCount: "devices", onlineCount: "online", addressHeading: "Address / hostname / MAC", status: "Status", response: "Response", actions: "Actions", filters: "Device filters",
    addDevice: "Add device", totalDevices: "Total devices", savedDevices: "Saved consoles", online: "Online", offline: "Offline",
    unknown: "Unchecked", unavailable: "Unchecked / offline", webReachable: "Web interface reachable", keepRecords: "Your devices stay saved",
    discoveryTitle: "Auto-scan every {seconds} s", scan: "Scan devices", scanning: "Scanning…",
    scanProgress: "Finding and verifying devices…", disabled: "Auto-discovery disabled", disabledHint: "You can add devices manually.",
    all: "All", emptyTitle: "No devices yet", emptyHint: "Enable mDNS on your NanoKVMs, then scan for devices. Or add an address yourself.",
    manualAdd: "Add your first device", noResults: "No matching devices", noResultsHint: "Try another search or change the device filter.",
    statusNote: "Online means the web interface responds, not that the attached computer or HDMI signal is on.", openConsole: "Open console", name: "Device name",
    url: "Device URL", urlHelp: "LAN IPs, hostnames, and NanoKVM's self-signed HTTPS are supported.", notes: "Notes", favoriteDevice: "Add to favorites",
    removeDevice: "Remove device", cancel: "Cancel", save: "Save device", saving: "Saving…", settings: "Dashboard settings", appearance: "Appearance",
    appearanceHint: "Make the dashboard feel at home.", lightTheme: "Use light theme", darkTheme: "Use dark theme", backup: "Device backup",
    backupHint: "Export names, URLs, notes, and favorites. Import merges with existing devices.", export: "Export JSON", import: "Import JSON",
    discoverySettings: "Auto-discovery", restoreDiscovery: "Rediscover removed devices", noDevices: "Can't find a device?",
    discoveryHelp: "Enable mDNS in NanoKVM Settings → Device. Use Host networking on Unraid. On multi-NIC hosts, set MDNS_INTERFACES to your LAN IPv4 address.",
    identityHelp: "Wired and Wi-Fi addresses sharing an mDNS hostname are grouped. Give different devices unique hostnames.",
    privacy: "The dashboard only reads device pages. It stores no NanoKVM passwords and sends no power, keyboard, or mouse commands.", confirmRemove: "Remove device",
    editDevice: "Edit device", copy: "Copy URL", copied: "URL copied", saved: "Device saved", removed: "Device removed", restored: "Discovery ignore list cleared",
    imported: "Device backup imported", importError: "Choose a valid device JSON backup.", fileLarge: "Backup files must be smaller than 1 MB.",
    manual: "Manual", discovered: "mDNS", noNotes: "No notes yet", lastSeen: "Last online", neverSeen: "Waiting for the first status check",
    refresh: "Refresh status", connectionError: "Can't reach the dashboard backend. Showing previous results. Check that the container is running.", requestError: "Request failed",
    search: "Search names, addresses, MACs, or notes", notesPlaceholder: "Which computer is connected to this KVM?", namePlaceholder: "For example, kvm-server",
    macHint: "Last received mDNS MACs; not mapped to specific IPs or wired / Wi-Fi interfaces.",
    macMissingHint: "No MAC address has been received in this device's mDNS advertisements.",
    removePrompt: "Remove this device? Discovered devices will be ignored until you restore them in Settings.", neverScanned: "Waiting for the first scan.",
    scanned: "Last scan", candidateLabel: "service hosts", verifiedLabel: "NanoKVMs", interval: "Discovery interval", seconds: "seconds",
    interfaces: "Interfaces", allInterfaces: "All available interfaces", addresses: "Discovered addresses", scanFailed: "Discovery failed", justNow: "just now",
  },
};

function preference(key, fallback) {
  try { return localStorage.getItem(key) || fallback; } catch { return fallback; }
}
function savePreference(key, value) {
  try { localStorage.setItem(key, value); } catch { /* Preferences are optional. */ }
}
const state = {
  language: preference("nanokvm-language", navigator.language.startsWith("zh") ? "zh" : "en"),
  theme: preference("nanokvm-theme", "dark"), devices: [], discovery: {}, filter: "all",
  search: "", editing: null, deleting: null, toastTimer: null, loading: false, rendered: "",
};
if (!(state.language in translations)) state.language = "en";
if (!["dark", "light"].includes(state.theme)) state.theme = "dark";
const t = (key) => translations[state.language][key] || key;

function timeAgo(value) {
  if (!value) return "";
  const seconds = Math.max(0, (Date.now() - Date.parse(value)) / 1000);
  if (seconds < 60) return t("justNow");
  const [divisor, unit] = seconds < 3600 ? [60, "minute"] : seconds < 86400 ? [3600, "hour"] : [86400, "day"];
  return new Intl.RelativeTimeFormat(state.language === "zh" ? "zh-CN" : "en", { numeric: "auto" }).format(-Math.floor(seconds / divisor), unit);
}

function translate(root = document) {
  $$('[data-i18n]', root).forEach((element) => { element.textContent = t(element.dataset.i18n); });
}

function renderPreferences() {
  document.documentElement.dataset.theme = state.theme;
  document.documentElement.lang = state.language === "zh" ? "zh-CN" : "en";
  translate();
  $("#language").textContent = state.language === "zh" ? "EN" : "中文";
  $("#theme-toggle").textContent = t(state.theme === "dark" ? "lightTheme" : "darkTheme");
  $("#search").placeholder = t("search");
  $("#search").setAttribute("aria-label", t("search"));
  $("#device-notes").placeholder = t("notesPlaceholder");
  $("#device-name").placeholder = t("namePlaceholder");
  $("#settings-open").title = t("settings");
  $("#settings-open").setAttribute("aria-label", t("settings"));
  $("#refresh").title = t("refresh");
  $("#refresh").setAttribute("aria-label", t("refresh"));
  $(".filters").setAttribute("aria-label", t("filters"));
  $(".device-table").setAttribute("aria-label", t("heading"));
  state.rendered = "";
  render();
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { ...(options.body ? { "Content-Type": "application/json" } : {}), ...options.headers },
  });
  if (!response.ok) {
    let message = `${t("requestError")} (${response.status})`;
    try {
      const data = await response.json();
      if (typeof data.detail === "string") message = data.detail;
      else if (Array.isArray(data.detail)) message = data.detail.map((item) => item.msg).join("; ");
    } catch { /* Use the HTTP status when the response is not JSON. */ }
    throw new Error(message);
  }
  return response.json();
}

function toast(message) {
  clearTimeout(state.toastTimer);
  $("#toast").textContent = message;
  $("#toast").classList.remove("hidden");
  state.toastTimer = setTimeout(() => $("#toast").classList.add("hidden"), 4000);
}

async function load() {
  if (state.loading) return;
  state.loading = true;
  try {
    const result = await api("/api/devices");
    state.devices = result.devices;
    state.discovery = result.discovery;
    $("#app-version").textContent = `v${result.version}`;
    $("#connection-error").classList.add("hidden");
    render();
  } catch {
    $("#connection-error").textContent = t("connectionError");
    $("#connection-error").classList.remove("hidden");
  } finally { state.loading = false; }
}

function render() {
  const online = state.devices.filter((device) => device.status === "online").length;
  $("#device-total").textContent = `${state.devices.length} ${t("deviceCount")}`;
  $("#device-online").textContent = `${online} ${t("onlineCount")}`;
  $("#count-all").textContent = state.devices.length;
  $("#count-online").textContent = online;
  $("#count-offline").textContent = state.devices.filter((device) => device.status === "offline").length;
  $("#count-favorites").textContent = state.devices.filter((device) => device.favorite).length;
  const discovery = state.discovery;
  $(".discovery-panel").classList.toggle("scanning", !!discovery.scanning);
  $(".discovery-panel").classList.toggle("disabled", discovery.enabled === false);
  $(".discovery-panel").classList.toggle("failed", !!discovery.error);
  $("#scan").disabled = !!discovery.scanning || discovery.enabled === false;
  $("#scan span").textContent = t(discovery.scanning ? "scanning" : "scan");
  $("#refresh").classList.toggle("busy", !!discovery.refreshing);
  $("#discovery-title").textContent = t(discovery.enabled === false ? "disabled" : "discoveryTitle").replace("{seconds}", discovery.interval || 60);
  let message = t("neverScanned");
  if (discovery.enabled === false) message = t("disabledHint");
  else if (discovery.scanning) message = t("scanProgress");
  else if (discovery.error) message = `${t("scanFailed")}: ${discovery.error}`;
  else if (discovery.last_scan) message = `${t("scanned")} ${timeAgo(discovery.last_scan)} · ${discovery.candidates} ${t("candidateLabel")} · ${discovery.verified} ${t("verifiedLabel")}`;
  $("#discovery-message").textContent = message;
  $("#discovery-settings-info").textContent = `${t("interval")}: ${discovery.interval || 60} ${t("seconds")} · ${t("interfaces")}: ${discovery.interfaces?.join(", ") || t("allInterfaces")}`;
  $$(".filter").forEach((button) => {
    const active = button.dataset.filter === state.filter;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });

  const visible = state.devices.filter((device) => {
    const haystack = [device.name, device.url, device.hostname, device.notes, ...(device.addresses || []), ...(device.mac_addresses || [])].join(" ").toLowerCase();
    const matchesFilter = state.filter === "all" || (state.filter === "favorites" ? device.favorite : device.status === state.filter);
    return matchesFilter && haystack.includes(state.search.toLowerCase());
  });
  $(".device-table").classList.toggle("hidden", visible.length === 0);
  $("#empty-state").classList.toggle("hidden", visible.length > 0);
  const filtered = state.devices.length > 0;
  $("#empty-title").textContent = t(filtered ? "noResults" : "emptyTitle");
  $("#empty-message").textContent = t(filtered ? "noResultsHint" : "emptyHint");
  $("#empty-add").classList.toggle("hidden", filtered);

  const signature = JSON.stringify([visible, state.language]);
  if (signature === state.rendered) return;
  state.rendered = signature;
  const fragment = document.createDocumentFragment();
  for (const device of visible) {
    const card = $("#device-template").content.cloneNode(true);
    translate(card);
    $(".device-row", card).dataset.id = device.id;
    $(".device-name", card).textContent = device.name;
    $(".device-name", card).title = `${t("openConsole")}: ${device.name}`;
    $(".device-name", card).href = device.url;
    $(".device-hostname", card).textContent = device.hostname || "";
    $(".device-hostname", card).title = device.hostname || "";
    $(".device-address", card).textContent = device.url;
    $(".device-address", card).title = `${device.url}\n${t("addresses")}: ${(device.addresses || []).join(", ")}`;
    const macs = device.mac_addresses || [];
    $(".device-macs", card).textContent = macs.length ? macs.join("\n") : "—";
    $(".device-macs", card).title = t(macs.length ? "macHint" : "macMissingHint");
    $(".device-notes", card).textContent = device.notes || "—";
    $(".device-notes", card).title = device.notes || t("noNotes");
    $(".status-label", card).textContent = t(device.status);
    $(".status-badge .dot", card).classList.add(device.status);
    $(".status-badge", card).title = device.error || t(device.status === "online" ? "webReachable" : device.status);
    $(".source-badge", card).textContent = t(device.source === "mdns" ? "discovered" : "manual");
    $(".latency", card).textContent = device.status === "online" && device.latency_ms !== null ? `${device.latency_ms} ms` : "—";
    $(".last-seen", card).textContent = device.last_seen ? `${t("lastSeen")} ${timeAgo(device.last_seen)}` : t("neverSeen");
    $(".last-seen", card).classList.toggle("hidden", device.status === "online");
    $(".last-seen", card).title = device.last_checked ? new Date(device.last_checked).toLocaleString() : "";
    $(".open-console", card).href = device.url;
    const favorite = $(".favorite-button", card);
    favorite.classList.toggle("selected", device.favorite);
    favorite.setAttribute("aria-label", `${t("favoriteDevice")}: ${device.name}`);
    favorite.setAttribute("aria-pressed", String(device.favorite));
    favorite.addEventListener("click", () => toggleFavorite(device));
    const copy = $(".copy-button", card);
    copy.title = t("copy"); copy.setAttribute("aria-label", t("copy"));
    copy.addEventListener("click", () => copyUrl(device.url));
    const edit = $(".edit-button", card);
    edit.title = t("editDevice"); edit.setAttribute("aria-label", `${t("editDevice")}: ${device.name}`);
    edit.addEventListener("click", () => openDevice(device));
    fragment.append(card);
  }
  $("#device-list").replaceChildren(fragment);
}

async function toggleFavorite(device) {
  try {
    await api(`/api/devices/${encodeURIComponent(device.id)}`, { method: "PUT", body: JSON.stringify({
      name: device.name, url: device.url, notes: device.notes, favorite: !device.favorite,
    }) });
    await load();
  } catch (error) { toast(error.message); }
}

async function copyUrl(value) {
  try {
    if (navigator.clipboard && window.isSecureContext) await navigator.clipboard.writeText(value);
    else {
      const input = document.createElement("textarea");
      input.value = value; input.className = "clipboard-fallback";
      document.body.append(input); input.select();
      const copied = document.execCommand("copy");
      input.remove();
      if (!copied) throw new Error(t("requestError"));
    }
    toast(t("copied"));
  } catch (error) { toast(error.message); }
}

function openDevice(device = null) {
  state.editing = device;
  $("#device-form").reset();
  $("#device-dialog-title").textContent = t(device ? "editDevice" : "addDevice");
  $("#device-name").value = device?.name || "";
  $("#device-url").value = device?.url || "";
  $("#device-notes").value = device?.notes || "";
  $("#device-favorite").checked = device?.favorite || false;
  $("#device-delete").classList.toggle("hidden", !device);
  $("#form-error").classList.add("hidden");
  $("#device-dialog").showModal();
  $("#device-name").focus();
}

$("#device-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = $("#device-save");
  button.disabled = true; button.textContent = t("saving");
  const data = { name: $("#device-name").value, url: $("#device-url").value,
    notes: $("#device-notes").value, favorite: $("#device-favorite").checked };
  try {
    const path = state.editing ? `/api/devices/${encodeURIComponent(state.editing.id)}` : "/api/devices";
    await api(path, { method: state.editing ? "PUT" : "POST", body: JSON.stringify(data) });
    $("#device-dialog").close();
    toast(t("saved")); await load();
  } catch (error) {
    $("#form-error").textContent = error.message; $("#form-error").classList.remove("hidden");
  } finally { button.disabled = false; button.textContent = t("save"); }
});

$("#device-delete").addEventListener("click", () => {
  state.deleting = state.editing;
  $("#confirm-message").textContent = `${state.deleting.name} — ${t("removePrompt")}`;
  $("#device-dialog").close(); $("#confirm-dialog").showModal();
});
$("#confirm-delete").addEventListener("click", async () => {
  if (!state.deleting) return;
  const button = $("#confirm-delete"); button.disabled = true;
  try {
    await api(`/api/devices/${encodeURIComponent(state.deleting.id)}`, { method: "DELETE" });
    $("#confirm-dialog").close(); state.deleting = null; toast(t("removed")); await load();
  } catch (error) { toast(error.message); }
  finally { button.disabled = false; }
});

$("#add-open").addEventListener("click", () => openDevice());
$("#empty-add").addEventListener("click", () => openDevice());
$("#settings-open").addEventListener("click", () => $("#settings-dialog").showModal());
$$(".dialog-close").forEach((button) => button.addEventListener("click", () => button.closest("dialog").close()));
$("#scan").addEventListener("click", async () => {
  $("#scan").disabled = true;
  try { await api("/api/discovery", { method: "POST" }); await load(); }
  catch (error) { toast(error.message); $("#scan").disabled = false; }
});
$("#refresh").addEventListener("click", async () => {
  try { await api("/api/refresh", { method: "POST" }); await load(); }
  catch (error) { toast(error.message); }
});
$("#restore-discovery").addEventListener("click", async () => {
  try { await api("/api/discovery/restore", { method: "POST" }); toast(t("restored")); await load(); }
  catch (error) { toast(error.message); }
});
$("#search").addEventListener("input", (event) => { state.search = event.target.value; render(); });
$$(".filter").forEach((button) => button.addEventListener("click", () => { state.filter = button.dataset.filter; render(); }));
$("#language").addEventListener("click", () => {
  state.language = state.language === "zh" ? "en" : "zh";
  savePreference("nanokvm-language", state.language); renderPreferences();
});
$("#theme-toggle").addEventListener("click", () => {
  state.theme = state.theme === "dark" ? "light" : "dark";
  savePreference("nanokvm-theme", state.theme); renderPreferences();
});
$("#export").addEventListener("click", async () => {
  try {
    const data = await api("/api/export");
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
    const link = document.createElement("a"); link.href = url; link.download = "nanokvm-devices.json";
    document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (error) { toast(error.message); }
});
$("#import").addEventListener("click", () => $("#import-file").click());
$("#import-file").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    if (file.size > 1024 * 1024) throw new Error(t("fileLarge"));
    const data = JSON.parse(await file.text());
    await api("/api/import", { method: "POST", body: JSON.stringify(data) });
    toast(t("imported")); await load();
  } catch (error) { toast(error instanceof SyntaxError ? t("importError") : error.message); }
  finally { event.target.value = ""; }
});
document.addEventListener("keydown", (event) => {
  if ($("dialog[open]") || ["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) return;
  if (event.key === "/" || ((event.metaKey || event.ctrlKey) && event.key === "k")) {
    event.preventDefault(); $("#search").focus();
  }
});
document.addEventListener("visibilitychange", () => { if (!document.hidden) load(); });
renderPreferences();
load();
setInterval(() => { if (!document.hidden) load(); }, 5000);
