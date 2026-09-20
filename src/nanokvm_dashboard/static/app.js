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
    controlTitle: "设备控制", username: "用户名", password: "密码",
    hostLabel: "主机", powerOn: "已开机", powerOff: "已关机", powerUnknown: "未知",
    controlCredentials: "NanoKVM 登录", credentialsSaved: "已保存 {username} 的凭据，可以控制这台设备。",
    credentialsMissing: "尚未保存凭据。保存后即可读取电源灯状态，并发送电源、重启和文本命令。",
    saveCredentials: "保存凭据", saveCredentialsBusy: "验证中…", clearCredentials: "清除凭据",
    passwordHelp: "密码加密保存在数据目录，只用于面板自行登录设备；不会回传到浏览器。",
    credentialsSavedToast: "凭据已保存，控制功能已启用", credentialsCleared: "已清除凭据",
    clearCredentialsPrompt: "清除后，面板不再读取这台设备的电源灯状态，也不能再发送电源、重启或文本命令。",
    powerTitle: "电源与重启", powerButton: "电源键", powerLong: "长按电源键", resetButton: "重启键",
    powerButtonHint: "短按：等同于按一次机箱电源键。系统启用 ACPI 电源键关机时会正常关机，否则可能直接断电。",
    powerLongHint: "按住约 5 秒：强制断电。系统不会收到任何通知，未保存的数据会丢失。",
    resetButtonHint: "直接拉主板 Reset 线：等同于按机箱上的重启键。操作系统不会收到关机信号，未保存的数据会丢失。",
    powerHint: "每次操作都会先确认。短按电源键＝按一次机箱电源键；长按约 5 秒＝强制断电；重启键＝直接拉主板 Reset，系统不会收到通知，未保存的数据会丢失。",
    pasteTitle: "发送文本", pasteSend: "发送文本", pastePlaceholder: "要输入到受控电脑的文本",
    pasteHint: "以 USB 键盘输入目标电脑，最多 1024 个字符；发送前请确认光标在正确的输入位置。无法输入中日韩字符。",
    pasteSent: "文本已发送", pasteEmpty: "请输入要发送的文本",
    controlFootnote: "电源与键鼠命令直接发送到这台 KVM，会立即影响它连接的那台电脑。",
    controlWarningTitle: "控制功能已启用，但面板没有登录保护",
    controlWarningText: "任何能访问这个面板的人都能开关受控电脑或向它输入文本。建议设置 DASHBOARD_USERNAME 和 DASHBOARD_PASSWORD，或只在可信网络内使用。",
    powerSent: "已发送电源键脉冲", resetSent: "已发送重启键脉冲",
    confirmPowerTitle: "发送电源键脉冲", confirmPowerLongTitle: "长按电源键", confirmResetTitle: "发送重启键脉冲",
    confirmPower: "{name}：相当于按一次机箱电源键，受控电脑会开机或关机。",
    confirmPowerLong: "{name}：按住电源键约 5 秒，通常会强制关机，可能丢失未保存的数据。",
    confirmReset: "{name}：等于按一次重启键，电脑会立即重启，未保存的数据可能丢失。",
    confirmSend: "发送", controlDisabled: "本次部署已关闭控制功能（ALLOW_CONTROL=false）。",
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
    controlTitle: "Device control", username: "Username", password: "Password",
    hostLabel: "Host", powerOn: "Powered on", powerOff: "Powered off", powerUnknown: "Unknown",
    controlCredentials: "NanoKVM login", credentialsSaved: "Credentials saved for {username}; this device can be controlled.",
    credentialsMissing: "No credentials saved yet. Save them to read the power LED and send power, reset, and text commands.",
    saveCredentials: "Save credentials", saveCredentialsBusy: "Checking…", clearCredentials: "Clear credentials",
    passwordHelp: "The password is stored encrypted in the data directory and used only by the dashboard to log in. It is never sent back to the browser.",
    credentialsSavedToast: "Credentials saved; control enabled", credentialsCleared: "Credentials cleared",
    clearCredentialsPrompt: "After clearing, the dashboard stops reading this device's power LED and can no longer send power, reset, or text commands.",
    powerTitle: "Power and reset", powerButton: "Power button", powerLong: "Hold power", resetButton: "Reset button",
    powerButtonHint: "Short press: same as tapping the case power button. The machine shuts down cleanly if its OS handles the ACPI power button, otherwise power may cut immediately.",
    powerLongHint: "Holding ~5 s: forced power cut. The OS is not notified and unsaved data is lost.",
    resetButtonHint: "Pulls the mainboard reset line: same as the case reset button. The OS is not notified and unsaved data is lost.",
    powerHint: "Every action asks first. Short press = a tap on the case power button; hold ~5 s = forced power cut; reset = a direct mainboard reset, so the OS is never told and unsaved data is lost.",
    pasteTitle: "Send text", pasteSend: "Send text", pastePlaceholder: "Text to type on the attached computer",
    pasteHint: "Types the text as USB keyboard input, up to 1024 characters. Check that the cursor is in the right place first; CJK characters cannot be typed.",
    pasteSent: "Text sent", pasteEmpty: "Enter the text to send",
    controlFootnote: "Power and keyboard commands go straight to this KVM and act on the computer it is wired to.",
    controlWarningTitle: "Control is enabled but this dashboard has no login",
    controlWarningText: "Anyone who can reach this dashboard can power the attached computers on or off or type into them. Set DASHBOARD_USERNAME and DASHBOARD_PASSWORD, or keep it on a trusted network.",
    powerSent: "Power pulse sent", resetSent: "Reset pulse sent",
    confirmPowerTitle: "Send a power pulse", confirmPowerLongTitle: "Hold the power button", confirmResetTitle: "Send a reset pulse",
    confirmPower: "{name}: like pressing the case power button once. The computer turns on or off.",
    confirmPowerLong: "{name}: holds the power button for about 5 seconds, which usually forces a power-off and can lose unsaved work.",
    confirmReset: "{name}: like pressing the reset button. The computer restarts immediately and unsaved work can be lost.",
    confirmSend: "Send", controlDisabled: "Control is disabled in this deployment (ALLOW_CONTROL=false).",
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
  search: "", editing: null, toastTimer: null, loading: false, rendered: "",
  controlAvailable: false, dashboardAuth: true, controlling: null, confirmAction: null,
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
  $$('[data-i18n-title]', root).forEach((element) => { element.title = t(element.dataset.i18nTitle); });
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
  $("#control-paste").placeholder = t("pastePlaceholder");
  if (state.controlling && $("#control-dialog").open) renderControlDevice(state.controlling);
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
    state.controlAvailable = result.control_available !== false;
    state.dashboardAuth = result.dashboard_auth !== false;
    if (state.controlling) {
      // Keep an open control dialog in step with the periodic status refresh.
      state.controlling = state.devices.find((item) => item.id === state.controlling.id) || null;
      if (state.controlling && $("#control-dialog").open) renderControlDevice(state.controlling);
    }
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
  // Controlling machines from a dashboard anyone on the network can open deserves a warning.
  $("#control-warning").classList.toggle(
    "hidden",
    !(state.controlAvailable && !state.dashboardAuth && state.devices.some((device) => device.control)),
  );

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
    // The device's own app version, only known once credentials are stored.
    $(".device-version", card).textContent = device.app_version ? `app ${device.app_version}` : "";
    $(".device-notes", card).textContent = device.notes || "—";
    $(".device-notes", card).title = device.notes || t("noNotes");
    $(".status-label", card).textContent = t(device.status);
    $(".status-badge .dot", card).classList.add(device.status);
    $(".status-badge", card).title = device.error || t(device.status === "online" ? "webReachable" : device.status);
    // The power LED says whether the attached computer is on, which the web probe cannot know.
    const power = $(".device-power", card);
    power.classList.toggle("hidden", !device.control);
    power.textContent = device.control ? `${t("hostLabel")} ${t(powerKey(device.power_state))}` : "";
    power.classList.toggle("power-on", device.power_state === "on");
    power.title = device.control_error || "";
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
    const control = $(".control-button", card);
    control.title = state.controlAvailable ? t("controlTitle") : t("controlDisabled");
    control.setAttribute("aria-label", `${t("controlTitle")}: ${device.name}`);
    control.classList.toggle("selected", !!device.control);
    control.disabled = !state.controlAvailable;
    control.addEventListener("click", () => openControl(device));
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

function powerKey(value) {
  return value === "on" ? "powerOn" : value === "off" ? "powerOff" : "powerUnknown";
}

function askConfirm(title, message, accept, action) {
  state.confirmAction = action;
  $("#confirm-title").textContent = title;
  $("#confirm-message").textContent = message;
  $("#confirm-accept").textContent = accept;
  $("#confirm-dialog").showModal();
}

function renderControlDevice(device) {
  if (!device) return;
  const power = device.power_state || "";
  $("#control-power").textContent = t(powerKey(power));
  $("#control-dialog .status-badge .dot").className = power === "on" ? "dot online" : "dot";
  const detail = [
    device.app_version ? `app ${device.app_version}` : "", device.control_error || "",
  ].filter(Boolean).join(" · ");
  $("#control-detail").textContent = detail;
  $("#control-detail").classList.toggle("hidden", !detail);
  $("#control-credentials-info").textContent = device.control
    ? t("credentialsSaved").replace("{username}", device.kvm_username || "")
    : t("credentialsMissing");
  $("#control-clear").classList.toggle("hidden", !device.control);
  // Power, reset and paste stay unavailable until this device has stored credentials.
  ["#power-press", "#power-long", "#reset-press", "#paste-send"].forEach((selector) => {
    $(selector).disabled = !device.control;
  });
}

function openControl(device) {
  state.controlling = device;
  $("#control-device").textContent = `${device.name} · ${device.url}`;
  $("#control-username").value = device.kvm_username || "";
  $("#control-password").value = "";
  $("#control-paste").value = "";
  $("#control-error").classList.add("hidden");
  renderControlDevice(device);
  $("#control-dialog").showModal();
}

function controlError(message) {
  $("#control-error").textContent = message;
  $("#control-error").classList.remove("hidden");
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
  const device = state.editing;
  $("#device-dialog").close();
  askConfirm(
    t("removeDevice"), `${device.name} — ${t("removePrompt")}`, t("confirmRemove"),
    async () => {
      await api(`/api/devices/${encodeURIComponent(device.id)}`, { method: "DELETE" });
      toast(t("removed")); await load();
    },
  );
});
$("#confirm-accept").addEventListener("click", async () => {
  const action = state.confirmAction;
  if (!action) return;
  const button = $("#confirm-accept"); button.disabled = true;
  try {
    await action();
    state.confirmAction = null; $("#confirm-dialog").close();
  } catch (error) { toast(error.message); }
  finally { button.disabled = false; }
});

$("#control-save").addEventListener("click", async () => {
  const device = state.controlling;
  if (!device) return;
  const username = $("#control-username").value.trim();
  const password = $("#control-password").value;
  const button = $("#control-save");
  if (!username || !password) { controlError(t("credentialsMissing")); return; }
  button.disabled = true; button.textContent = t("saveCredentialsBusy");
  try {
    state.controlling = await api(`/api/devices/${encodeURIComponent(device.id)}/control`, {
      method: "POST", body: JSON.stringify({ username, password }),
    });
    $("#control-password").value = "";
    $("#control-error").classList.add("hidden");
    toast(t("credentialsSavedToast"));
    renderControlDevice(state.controlling);
    await load();
  } catch (error) { controlError(error.message); }
  finally { button.disabled = false; button.textContent = t("saveCredentials"); }
});
$("#control-clear").addEventListener("click", () => {
  const device = state.controlling;
  if (!device) return;
  askConfirm(
    t("clearCredentials"), `${device.name} — ${t("clearCredentialsPrompt")}`, t("clearCredentials"),
    async () => {
      await api(`/api/devices/${encodeURIComponent(device.id)}/control`, { method: "DELETE" });
      state.controlling = { ...device, control: false, kvm_username: "" };
      $("#control-username").value = "";
      renderControlDevice(state.controlling);
      toast(t("credentialsCleared")); await load();
    },
  );
});

function sendPower(device, action, duration, title, message, done) {
  askConfirm(title, message, t("confirmSend"), async () => {
    await api(`/api/devices/${encodeURIComponent(device.id)}/power`, {
      method: "POST", body: JSON.stringify({ action, duration }),
    });
    toast(done);
    await load();
    renderControlDevice(state.controlling);
  });
}
$("#power-press").addEventListener("click", () => {
  const device = state.controlling;
  if (!device) return;
  sendPower(
    device, "power", null, t("confirmPowerTitle"),
    t("confirmPower").replace("{name}", device.name), t("powerSent"),
  );
});
$("#power-long").addEventListener("click", () => {
  const device = state.controlling;
  if (!device) return;
  sendPower(
    device, "power", 5000, t("confirmPowerLongTitle"),
    t("confirmPowerLong").replace("{name}", device.name), t("powerSent"),
  );
});
$("#reset-press").addEventListener("click", () => {
  const device = state.controlling;
  if (!device) return;
  sendPower(
    device, "reset", null, t("confirmResetTitle"),
    t("confirmReset").replace("{name}", device.name), t("resetSent"),
  );
});
$("#paste-send").addEventListener("click", async () => {
  const device = state.controlling;
  const text = $("#control-paste").value;
  if (!device) return;
  if (!text) { toast(t("pasteEmpty")); return; }
  const button = $("#paste-send"); button.disabled = true;
  try {
    await api(`/api/devices/${encodeURIComponent(device.id)}/paste`, {
      method: "POST", body: JSON.stringify({ text }),
    });
    $("#control-paste").value = "";
    toast(t("pasteSent"));
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
