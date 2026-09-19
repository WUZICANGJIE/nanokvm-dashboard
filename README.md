# NanoKVM Dashboard

一个轻量、自托管的 NanoKVM 设备面板：**mDNS 自动发现、设备归组、状态检查、一键打开控制台**。适合部署在 Unraid、NAS 或家中的 Linux 服务器。

[![CI](https://github.com/WUZICANGJIE/nanokvm-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/WUZICANGJIE/nanokvm-dashboard/actions/workflows/ci.yml)

## 功能

- 自动浏览 `_workstation`、`_http`、`_https`、`_nanokvm`、`_ssh` mDNS 服务，并读取设备网页确认 NanoKVM 身份。
- 支持 NanoKVM Cube / PCIe 和 Pro 的常见 Avahi 广播；不需要 DHCP 上报 hostname。
- 同一 mDNS 主机名的多个地址归为一台设备；地址变化后保留名称、备注和收藏。
- 手动添加 HTTP / HTTPS 地址；支持 NanoKVM 默认的自签名证书。
- 后端检查 Web 页面是否可达，显示延迟、上次在线时间和错误原因。
- 搜索、收藏、在线筛选、深浅主题、中英文界面、JSON 导入导出。
- 简洁的设备表格，集中显示地址、状态、响应时间和备注；手机上自动改为纵向排列。
- SQLite 持久化，更新容器不会丢失设备列表。
- 不保存 KVM 密码，不代理登录，不发送电源、键鼠或配置修改命令。

> “在线”仅表示管理网页能响应，不代表被控电脑已开机或存在 HDMI 信号。控制台在新标签页直接打开，使用 NanoKVM 自己的登录。

## Unraid 安装

Docker Hub 镜像发布后使用：

```text
wuzicangjie/nanokvm-dashboard:latest
```

在 **Docker → Add Container** 填写：

| 项目 | 值 |
|---|---|
| Name | `nanokvm-dashboard` |
| Repository | `wuzicangjie/nanokvm-dashboard:latest` |
| Network Type | **Host** |
| WebUI | `http://[IP]:[PORT:8080]/` |
| Path: 容器路径 | `/data` |
| Path: 主机路径 | `/mnt/user/appdata/nanokvm-dashboard` |
| Variable: `PUID` | `99` |
| Variable: `PGID` | `100` |
| Variable: `PORT` | `8080`，如果占用可换成 `8999` 等 |

运行后访问 `http://Unraid的IP:8080`。Host 模式直接使用 `PORT`，不用添加端口映射。如果改为 8999，WebUI 也改为 `http://[IP]:8999/`。

**自动发现需要：**

1. 在每台 NanoKVM 的 **Settings → Device → mDNS** 中开启 mDNS。
2. 容器与设备位于能够互通 mDNS 组播的 LAN。Host 网络避免 Docker 默认 bridge 隔离组播。
3. 如果 Unraid 有多张网卡，增加 `MDNS_INTERFACES`，填写 **Unraid 自己 LAN 网卡的 IPv4 地址**，例如 `192.168.1.10`。不是 NanoKVM 的地址，也不是网卡名称 `br0`。
4. 等待首次扫描完成，或点击“扫描设备”。状态栏显示服务主机数与确认的 NanoKVM 数。

可以使用 [`unraid/nanokvm-dashboard.xml`](unraid/nanokvm-dashboard.xml) 作为手动模板，导入前检查路径和端口。

## Docker Compose

```sh
docker compose up -d
```

参见 [`compose.yaml`](compose.yaml)。在 Linux 上使用 host 网络模式，无需 privileged 或额外 capabilities。默认 UID/GID 为 Unraid 的 `99:100`，可通过 PUID/PGID 修改。

更新镜像：

```sh
docker compose pull
docker compose up -d
```

Unraid 用户可在 Docker 页面检查并安装镜像更新。GitHub 推送触发镜像发布，不会直接替换你正在运行的容器。

## 配置变量

| 环境变量 | 默认 | 说明 |
|---|---|---|
| `PORT` | `8080` | 容器 HTTP 监听端口 |
| `DATA_DIR` | `/data`（镜像内） | 数据库目录 |
| `PUID` / `PGID` | `99` / `100` | 镜像运行用户，首次启动会调整数据目录属主 |
| `MDNS_ENABLED` | `true` | 是否开启自动发现 |
| `MDNS_INTERFACES` | 空 | 逗号分隔的本机 IPv4 地址；空表示所有可用网卡 |
| `DISCOVERY_INTERVAL` | `60` | 自动扫描间隔，最少 15 秒 |
| `DISCOVERY_SECONDS` | `5` | 每次 mDNS 浏览持续时间，2–30 秒；网页确认另需少量时间 |
| `PROBE_INTERVAL` | `30` | 状态检查间隔，最少 10 秒 |
| `PROBE_TIMEOUT` | `3` | 单次 HTTP 请求超时，1–15 秒 |
| `DASHBOARD_USERNAME` | 空 | 可选的面板 HTTP Basic Auth 用户名 |
| `DASHBOARD_PASSWORD` | 空 | 与用户名同时设置；不属于 NanoKVM 登录信息 |

默认面向可信 LAN，不要求登录。需要面板认证时同时设置两项，跨不可信网络访问应在 HTTPS 反向代理后使用。`/healthz` 不包含设备信息，供容器健康检查使用。

服务绑定 `0.0.0.0`；mDNS 浏览使用 IPv4 组播，支持记录中的私有 IPv4、Tailscale IPv4 和 IPv6 ULA。手动目标仅允许这些网段，DNS 解析后的地址也会再次验证。公网地址、loopback、链路本地地址不在当前版本支持范围内。

## 发现行为与限制

- **不会扫描整个 IP 地址段。** 只浏览 mDNS 服务，再对服务公布的地址读取网页；不探测视频、不提交登录。
- 设备改成自定义名称也能通过网页识别，不要求主机名以 `kvm-` 开头。
- 同一 hostname 的有线 / Wi-Fi 地址可以合并，但前提是它们确实公布相同的 mDNS 主机名。不同设备请用不同 hostname。
- 自动管理的设备 URL 可随发现更新。编辑访问地址后会采用你的自定义 URL，不再自动覆盖。
- 手动填入 `.local` 地址时，如果已通过 mDNS 发现该主机，可用已发现地址检查状态；否则取决于容器的系统 DNS 解析。手动 IP 地址不依赖这一条件。
- 页面受额外认证保护或被反向代理完全改写时，可能无法自动识别；可以手动添加。
- 移除自动发现设备会将它加入忽略列表，避免下次扫描立即出现。可在设置中选择“重新发现已移除的设备”。
- 导入是按 URL 合并，不删除现有设备。导出仅包含名称、URL、备注和收藏，不含临时状态和忽略列表。
- 本项目是独立的社区工具，不是 Sipeed 官方 NanoKVM Admin。

## 本地开发

需要 Python 3.12+ 和 [uv](https://docs.astral.sh/uv/)。

```sh
uv sync --frozen
uv run uvicorn nanokvm_dashboard.app:app --host 0.0.0.0 --port 8080
```

静态前端没有 npm 依赖，也不依赖外部 CDN。后端以 Python wheel 打包，静态文件包含在 wheel 中。

```sh
uv run ruff check .
uv run pytest
uv build
```

浏览器端到端检查：

```sh
uv sync --frozen --group browser
uv run playwright install chromium
uv run python scripts/browser_smoke.py
```

NixOS 上可使用 `nix-shell` 进入开发环境；浏览器测试可通过 `CHROMIUM_EXECUTABLE` 指定系统 Chromium。

在真实 LAN 上运行一次发现诊断（只发送 mDNS 查询和读取设备网页，结果不持久化）：

```sh
uv run python scripts/discover_once.py --interface 192.168.1.10
```

NixOS 开发 shell 中使用 `ruff check .`，避免运行 PyPI wheel 中针对通用 Linux 的 ruff 可执行文件。

## GitHub Actions → Docker Hub

CI 会运行 Python lint、测试、打包、浏览器检查、Docker 构建和容器健康检查。

发布前，在 GitHub 仓库中配置：

1. **Settings → Secrets and variables → Actions → Variables**：
   - `DOCKERHUB_USERNAME` = `wuzicangjie`
2. 同页面的 **Secrets**：
   - `DOCKERHUB_TOKEN` = Docker Hub 的 Read & Write 访问令牌。

工作流发布 `linux/amd64` 和 `linux/arm64` 镜像：

- 推送到 `main`：发布 `latest` 和 `sha-<commit>`。
- 推送 `v*` 版本标签：发布对应版本标签。
- 手动运行工作流：对 main 同样可以发布。
- PR：执行检查，不发布。
- 未配置 Docker Hub 令牌：仍执行构建测试，发布步骤明确跳过。

令牌始终由 GitHub Secrets 注入。不要把令牌写进仓库、Compose 文件或镜像。

## License

MIT. NanoKVM is a trademark/name of its respective owner.
