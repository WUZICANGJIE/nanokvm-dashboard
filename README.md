# NanoKVM Dashboard

一个轻量、自托管的 NanoKVM 设备面板：**mDNS 自动发现、设备归组、状态检查、一键打开控制台**。适合部署在 Unraid、NAS 或家中的 Linux 服务器。

[![CI](https://github.com/WUZICANGJIE/nanokvm-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/WUZICANGJIE/nanokvm-dashboard/actions/workflows/ci.yml)

## 功能

- 自动浏览 `_workstation`、`_http`、`_https`、`_nanokvm`、`_ssh` mDNS 服务，并读取设备网页确认 NanoKVM 身份。
- 支持 NanoKVM Cube / PCIe 和 Pro 的常见 Avahi 广播；不需要 DHCP 上报 hostname。
- 同一 mDNS 主机名的多个地址归为一台设备；地址变化后保留名称、备注和收藏。
- 在设备地址下方显示从 mDNS 获取的 MAC 地址，支持多个 MAC 和搜索。
- 手动添加 HTTP / HTTPS 地址；支持 NanoKVM 默认的自签名证书。
- 后端检查 Web 页面是否可达，显示延迟、上次在线时间和错误原因。
- 搜索、收藏、在线筛选、深浅主题、中英文界面、JSON 导入导出。
- 简洁的设备表格，集中显示地址、状态、响应时间和备注；手机上自动改为纵向排列。
- SQLite 持久化，更新容器不会丢失设备列表。
- 可选控制：为某台设备保存 NanoKVM 登录后，面板会显示它的电源灯状态和版本，并可发送电源键、长按电源键、重启键以及文本输入。
- 控制默认关闭：不保存凭据的设备仍然只做只读检查，面板也不会代理 NanoKVM 的登录页面。

> “在线”仅表示管理网页能响应，不代表被控电脑已开机或存在 HDMI 信号。控制台在新标签页直接打开，使用 NanoKVM 自己的登录。

## 设备控制（可选，默认关闭）

面板默认只读取设备网页。只有你在某台设备上显式保存了 NanoKVM 的登录凭据之后，这台设备才会多出以下能力：

- **状态**：通过设备自己的 API 读取电源灯（ATX 电源指示灯）和 HDD 灯，以及应用版本，显示在设备列表里。电源灯比“网页可达”更接近“这台电脑现在是开着的”。
- **电源与重启**：发送 ATX 按键脉冲，每次操作都会在面板上二次确认。短按电源键（800 ms）＝按一次机箱电源键；长按（5 s）＝强制断电；重启键＝直接拉主板 Reset 线。**重启键和长按都不经过操作系统**：系统收不到任何通知，未保存的数据会丢失。是否“正常关机”完全取决于被控系统对 ACPI 电源键的处理（启用后会优雅关机，否则可能直接断电）——固件本身不提供“优雅关机”接口。
- **发送文本**：以 USB 键盘输入目标电脑，最多 1024 个字符（设备的限制）。请先确认光标在正确位置；设备无法输入中日韩字符。

凭据处理方式：

- 保存时会先用这份凭据登录一次设备，登录失败不会保存。
- 密码用 Fernet 加密后存入数据目录的 SQLite（`/data/dashboard.db`），密钥在 `/data/credentials.key`（权限 600）。备份只包含数据库时无法还原密码；密钥丢失后需要重新填写。
- 面板只把密码用于自己登录设备，不写回浏览器、不写进 JSON 导出，也不会显示在列表里（只显示用户名）。
- 会话 token 只存在内存中，重启容器或用“清除凭据”后即失效。

安全边界要说清楚：

- 开启控制后，**任何能访问这个面板的人都能开关受控电脑或向它输入文本**。面板本身默认没有登录保护，所以请在设置 `DASHBOARD_USERNAME` / `DASHBOARD_PASSWORD` 之后，或在可信网络内使用；面板检测到“已配置控制但没有面板登录”时会在设置里提示。
- 需要彻底关闭控制能力时，设置 `ALLOW_CONTROL=false`，或在每台设备上清除凭据。
- 电源与键鼠命令直接作用于被控电脑，属于不可逆操作；长按电源键和重启键可能丢失未保存的数据。

## Unraid 安装

GHCR 镜像发布后使用：

```text
ghcr.io/wuzicangjie/nanokvm-dashboard:latest
```

在 **Docker → Add Container** 填写：

| 项目 | 值 |
|---|---|
| Name | `nanokvm-dashboard` |
| Repository | `ghcr.io/wuzicangjie/nanokvm-dashboard:latest` |
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
| `ALLOW_CONTROL` | `true` | 是否允许设备控制（电源/重启/文本与凭据保存）；设为 `false` 后相关接口返回 403 |
| `DASHBOARD_USERNAME` | 空 | 可选的面板 HTTP Basic Auth 用户名 |
| `DASHBOARD_PASSWORD` | 空 | 与用户名同时设置；不属于 NanoKVM 登录信息 |

默认面向可信 LAN，不要求登录。需要面板认证时同时设置两项，跨不可信网络访问应在 HTTPS 反向代理后使用。`/healthz` 不包含设备信息，供容器健康检查使用。

服务绑定 `0.0.0.0`；mDNS 浏览使用 IPv4 组播，支持记录中的私有 IPv4、Tailscale IPv4 和 IPv6 ULA。手动目标仅允许这些网段，DNS 解析后的地址也会再次验证。公网地址、loopback、链路本地地址不在当前版本支持范围内。

## 发现行为与限制

- **不会扫描整个 IP 地址段。** 只浏览 mDNS 服务，再对服务公布的地址读取网页；不探测视频。发现流程不提交登录，只有你在设备上保存凭据后，面板才会用它登录该设备。
- 设备改成自定义名称也能通过网页识别，不要求主机名以 `kvm-` 开头。
- 同一 hostname 的有线 / Wi-Fi 地址可以合并，但前提是它们确实公布相同的 mDNS 主机名。不同设备请用不同 hostname。
- MAC 来自 Avahi `_workstation` 服务名称中的 `hostname [MAC]`，只在设备通过现有网页确认流程后保存。未广播该信息的设备（包括尚未关联 mDNS 的手动设备）显示“—”，悬停可查看说明。不需要登录设备或额外容器权限。
- MAC 仅为设备广播的参考信息，不用于归组，也不推断它对应哪个 IP 或有线 / Wi-Fi 接口。显示最近一次获取的 MAC 集合；离线、重启或一次扫描未获取 MAC 时保留旧值，后续获取到非空集合时替换。MAC 不随 JSON 备份导出，导入后通过发现重新获取。已有数据库会自动升级。
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

控制相关的测试不接触真实设备：设备侧由进程内的假 NanoKVM 实现（同样的信封、cookie 与路由），登录密码的加密则用 `openssl` 命令行作为独立实现来核对。

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

## GitHub Actions → GHCR

CI 会运行 Python lint、测试、打包、浏览器检查、Docker 构建和容器健康检查。

镜像发布到 **GitHub Container Registry**（`ghcr.io/wuzicangjie/nanokvm-dashboard`），不需要配置任何 secret：工作流用仓库自带的 `GITHUB_TOKEN` 登录，`publish` job 已声明 `packages: write` 权限。

工作流发布 `linux/amd64` 和 `linux/arm64` 镜像：

- 推送到 `main`：发布 `latest` 和 `sha-<commit>`。
- 推送 `v*` 版本标签：发布对应版本标签。
- 手动运行工作流：对 main 同样可以发布。
- PR：执行检查，不发布。

首次发布后到 **Packages → 包设置** 确认可见性：设为 public 时任何人无需登录即可 `docker pull`；保持 private 则拉取方需要带 `read:packages` 权限的 GitHub 令牌。

从 Docker Hub 迁移过来的话：`compose.yaml`、Unraid 模板与本文档的镜像名都已改为 `ghcr.io/...`。只改镜像名不会影响正在运行的容器——Unraid 需要按模板**重建一次**容器，之后更新继续走 Docker 页面的检查更新。原 Docker Hub 仓库可以保留（旧镜像）或删除。

## License

MIT. NanoKVM is a trademark/name of its respective owner.
