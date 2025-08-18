import asyncio
from typing import List, Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("app_server")


@mcp.tool()
async def p1finger_scan(
    mode: str,
    target: Optional[str] = None,
    target_file: Optional[str] = None,
    output: Optional[str] = None,
    proxy: Optional[str] = None,
    rate: Optional[int] = 500,
    p1finger_args: Optional[List[str]] = None,
) -> str:
    """
    执行 P1finger 指纹识别工具,支持本地规则识别(rule)和 Fofa采集识别(fofa)两种模式。
    工具运行在 Linux 环境中，二进制名称为 p1finger,扫描完成后如果使用 -o 指定输出为 JSON/CSV,将自动打印文件内容至控制台，方便大模型读取分析。
    ===========================
    ✅ Usage 示例:
    ---------------------------
    本地模式扫描单个目标:p1finger rule -u http://example.com
    本地模式批量扫描（通过文件）并输出为 json:p1finger rule -f urls.txt -o result.json
    使用 Fofa 模式扫描:p1finger fofa -f targets.txt --proxy socks5://127.0.0.1:9000 -o result.csv
    ===========================
    ✅ 参数说明:
    ---------------------------
    mode (str):选择运行模式。必须为以下之一：
            - "rule"  使用本地指纹规则数据库
            - "fofa"  基于 Fofa 引擎进行远程识别
    target (str, 可选):
        单个目标 URL 或 IP(如 http://example.com)。不能与 target_file 同时为空。
    target_file (str, 可选):
        包含多个目标的文本文件路径，每行一个 URL。
    output (str, 可选):
        输出文件路径。支持 .csv 或 .json 格式。如果指定该字段，将自动在控制台 cat 出内容。
    proxy (str, 可选):
        使用代理进行请求（支持 socks5 或 http 代理），如：
            socks5://127.0.0.1:9000
            http://127.0.0.1:8000
    rate (int, 可选):
        控制并发数量，默认值为 500,用于调节扫描速度与系统负载。
    p1finger_args (List[str], 可选):
        额外参数（如 ["--debug"]）将追加至命令末尾。
    ===========================
    ✅ 自动行为说明:
    ---------------------------
    - 如果 output 指定了 JSON 或 CSV 文件，则程序将自动执行:cat <output_file>并将其内容输出到控制台，便于大模型读取结构化结果。
    ===========================
    ✅ P1finger 官方命令参考:
    ---------------------------
    可用子命令：
        rule       - 使用本地指纹库扫描
        fofa       - 使用 Fofa 引擎扫描
        upgrade    - 升级工具
        version    - 显示版本信息

    常用参数说明：
        -u <url>             扫描目标
        -f <file>            批量扫描目标文件
        -o <file>            输出文件（支持 .csv/.json)
        --proxy <proxy>      使用代理
        --rate <N>           设置并发协程数（默认 500)
        --debug              输出调试信息
    ===========================
    ✅ 返回值说明:
    ---------------------------
    - 返回控制台标准输出
    - 如果指定了输出文件，则附加其完整内容
    - 若发生错误，会包含具体异常信息
    """

    if mode not in ["rule", "fofa"]:
        return "Invalid mode. Use 'rule' or 'fofa'."

    cmd = ["p1finger", mode]

    if target:
        cmd += ["-u", target]
    elif target_file:
        cmd += ["-f", target_file]
    else:
        return "Error: You must provide either 'target' or 'target_file'."

    if output:
        cmd += ["-o", output]

    if proxy:
        cmd += ["--proxy", proxy]

    if rate:
        cmd += ["--rate", str(rate)]

    if p1finger_args:
        cmd += p1finger_args

    try:
        # Run P1finger scan
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        stdout_bytes, _ = await process.communicate()
        stdout = stdout_bytes.decode("utf-8", errors="replace")

        result = stdout

        # Automatically show output content if it's json/csv
        if output and (output.endswith(".json") or output.endswith(".csv")):
            try:
                cat_process = await asyncio.create_subprocess_exec("cat", output, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
                cat_stdout, _ = await cat_process.communicate()
                result += f"\n\n===== {output} Content =====\n{cat_stdout.decode('utf-8', errors='replace')}"
            except Exception as e:
                result += f"\n\n[!] Failed to read output file '{output}': {str(e)}"

        return result if process.returncode == 0 else f"P1finger exited with code {process.returncode}\nOutput:\n{result}"

    except Exception as e:
        return f"Failed to execute p1finger: {str(e)}"


@mcp.tool()
async def ehole_scan(url: str) -> str:
    """
    执行 EHole 指纹识别工具，固定模式 finger,需传入 URL。
    ===========================
    ✅ 参数说明:
    ---------------------------
    url (str): 必填，目标 URL，例如 http://192.168.254.130

    ===========================
    example: ehole finger -u url
    ✅ 返回值说明:
    ---------------------------
    - 返回控制台标准输出内容
    - 若失败,包含具体异常提示
    """
    if not url:
        return "Missing required parameter: url"

    cmd = ["ehole", "finger", "-u", url]

    try:
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        stdout_bytes, _ = await process.communicate()
        stdout = stdout_bytes.decode("utf-8", errors="replace")

        return stdout if process.returncode == 0 else f"EHole exited with code {process.returncode}\nOutput:\n{stdout}"

    except Exception as e:
        return f"Failed to execute ehole: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
