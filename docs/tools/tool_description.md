# tool_recon_port_scan.py

简介：端口扫描 MCP server 模块集成两个主流的端口扫描工具：nmap和masscan;主要用于端口扫描识别任务。

该程序注册了两个MCP工具接口：

| 工具名    | 功能描述                      | 特点与适用场景                         |
| --------- | ----------------------------- | -------------------------------------- |
| `nmap`    | 使用 Nmap 对目标执行端口扫描  | 功能全面，支持服务识别、操作系统识别等 |
| `masscan` | 使用 Masscan 进行高速端口扫描 | 扫描速度极快，适合大规模扫描任务       |

## nmap(target: str, nmap_args: List[str] = None) -> str

| 字段名    | 类型          | 必填 | 说明                                           | 示例                                                |
| :-------- | :------------ | :--- | :--------------------------------------------- | :-------------------------------------------------- |
| target    | string        | 是   | 支持主机名、IP、CIDR、范围等多种 Nmap 合法写法 | `"192.168.1.1"` `"scanme.nmap.org"` `"10.0.0.0/24"` |
| nmap_args | array[string] | 否   | 任意合法的 Nmap 命令行参数列表                 | `["-sS", "-p-", "-T4"]`                             |

 输出结果：Nmap 扫描结果文本或错误提示

Flow：

接收参数：target, nmap_args   --> 构造命令：["nmap"] + nmap_args + [target] --> 异步执行命令（asyncio.create_subprocess_exec） -->捕获输出 -->返回结果字符串。 MCP通信方式：通过 stdio 启动（mcp.run(transport="stdio")）

## masscan(target: str, ports: str = "1-65535", masscan_args: List[str] = None) -> str

| 字段名       | 类型          | 必填 | 说明                               | 示例                  |
| :----------- | :------------ | :--- | :--------------------------------- | :-------------------- |
| target       | string        | 是   | 目标 IP 地址或网络范围             | `"192.168.1.0/24"`    |
| ports        | string        | 否   | 要扫描的端口范围，默认为 "1-65535" | `"80,443"` `"1-100"`  |
| masscan_args | array[string] | 否   | 额外的 Masscan 命令行参数列表      | `["--rate", "10000"]` |

输出结果：Masscan 扫描结果文本或错误提示（提示需 root 权限）

Flow：
接收参数：target,ports,masscan_args   --> 构造命令：["masscan"] + masscan_args + [target, f"-p{ports}"] --> 异步执行命令（asyncio.create_subprocess_exec） -->捕获输出 -->返回结果字符串。 MCP通信方式：通过 stdio 启动（mcp.run(transport="stdio")

工具加载：

  "port_scan": {

   	 "command":"python",
   	
   	 "args":["src/ai_pentest/tools/tool_recon_port_scan.py"],
   	
   	  "transport": "stdio"
   	
   	}

# tool_recon_dir_enum.py

简介：Web 目录枚举模块，集成两种常见工具：`dirsearch` 和 `dirb`，用于识别网站的隐藏目录和敏感路径。

该程序注册了两个 MCP 工具接口：

| 工具名                     | 功能描述                      | 特点与适用场景                               |
| -------------------------- | ----------------------------- | -------------------------------------------- |
| `dirsearch_explosion_tool` | 使用 dirsearch 枚举 Web 路径  | 参数丰富、支持多种扩展、状态码、代理设置等   |
| `dirb`                     | 使用 dirb 对 URL 进行路径爆破 | 简洁实用，支持多字典、代理、自定义请求等场景 |

## dirsearch_explosion_tool(target: str, dirsearch_options: List[str] = None) -> str

| 字段名            | 类型          | 必填 | 说明                                                         | 示例                                                         |
| ----------------- | ------------- | ---- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| target            | string        | 是   | 目标网站 URL                                                 | `"http://192.168.1.1"`                                       |
| dirsearch_options | array[string] | 否   | dirsearch 支持的所有命令行参数（如 `-e`, `--exclude-status` 等） | `["-e", "php,html", "--exclude-status", "404", "--format", "json"]` |

输出结果：返回 dirsearch 扫描输出文件路径（如能识别），否则返回原始命令输出内容。

**Flow：**

接收参数：`target`, `dirsearch_options` → 构造命令：`dirsearch -u {target} {options}`
 → 执行命令（`subprocess.run`） → 尝试从 stdout 匹配输出文件路径 → 返回输出路径或原始输出文本

## dirb(target: str, wordlists: List[str] = None, dirb_args: List[str] = None) -> str

| 字段名    | 类型          | 必填 | 说明                                                     | 示例                                                         |
| --------- | ------------- | ---- | -------------------------------------------------------- | ------------------------------------------------------------ |
| target    | string        | 是   | 要扫描的目标 URL                                         | `"http://example.com"`                                       |
| wordlists | array[string] | 否   | 使用的字典路径（可多个，以逗号分隔），为空则使用默认字典 | `["/usr/share/dirb/wordlists/common.txt", "/tmp/custom.txt"]` |
| dirb_args | array[string] | 否   | 其他合法的 dirb 命令行参数                               | `["-X", ".php", "-o", "out.txt", "-a", "CustomAgent/1.0"]`   |

输出结果：返回 dirb 扫描结果（含成功或失败提示）

**Flow：**

接收参数：`target`, `wordlists`, `dirb_args` → 构造命令：`dirb {target} {wordlists} {options}`
 → 使用 `asyncio.create_subprocess_exec` 异步执行命令 → 读取 stdout 并返回执行结果

工具加载：

  "Dir_Enumerate": {

   	 "command":"python",
   	
   	 "args":["src/ai_pentest/tools/tool_recon_dir_enum.py"],
   	
   	  "transport": "stdio"
   	
   	}



# tool_recon_app_server.py





# tool_attack_web.py



## sqlmap(target: str, sqlmap_options: List[str] = None) -> str

| 字段名         | 类型          | 必填 | 说明                                     | 示例                                  |
| -------------- | ------------- | ---- | ---------------------------------------- | ------------------------------------- |
| target         | string        | 是   | 目标地址 URL，需带协议前缀（如 http://） | `"http://example.com/index.php?id=1"` |
| sqlmap_options | array[string] | 否   | 任意合法的 sqlmap 命令参数列表           | `["--batch", "--dbs"]`                |

输出结果：SQLMAP 工具执行的输出文本，包含扫描进度、发现的注入点、数据库信息等；若执行失败，返回错误提示信息。

**Flow：**

接收参数：`target`, `sqlmap_options` → 构造命令：`python sqlmap -u <target> <options>`
 → 执行命令（subprocess.run） → 捕获标准输出或标准错误 → 返回扫描结果或报错信息。







工具加载：

  "Web": {

   	 "command":"python",
   	
   	 "args":["src/ai_pentest/tools/tool_attack_web.py"],
   	
   	  "transport": "stdio"
   	
   	}



# tool_attack_ftp_ssh.py