import os
import subprocess
import time

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Web")


@mcp.tool()
async def katana_xray(url: str) -> str:
    """使用 xray 对目标进行漏洞扫描: 首先运行 katana 爬虫, 对目标 url 进行爬取, 然后将所有请求数据包发送到 xray, 进行漏洞扫描

    Args:
        url (str): 目标 url, 比如: http://www.example.com

    Returns:
        str: 扫描到的漏洞数据
    """
    # 在后台启动 xray
    file_path = "./data/result.json"
    xray_command = ["xray", "webscan", "--listen", "127.0.0.1:8080", "--json-output", file_path]
    print(f"正在启动 Xray, 启动命令: {' '.join(xray_command)}")

    try:
        xray_process = subprocess.Popen(xray_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # 使用 Popen 在后台启动进程
        print("Xray 进程已成功启动。等待 5 秒以确保 Xray 完全启动...")
        time.sleep(5)  # 等待 xray 启动

    except FileNotFoundError:
        return "错误: 'Xray' 命令未找到。请确保 Xray 已安装并已添加到系统 PATH。"

    except Exception as e:
        return f"启动 Xray 时发生未知错误: {e}"

    # 运行 katana 爬虫, 对目标 url 进行爬取, 并将所有请求数据包发送到 xray
    katana_command = ["katana", "-u", url, "-iqp", "-aff", "-fx", "-or", "-proxy", "http://127.0.0.1:8080"]
    print(f"正在启动 Katana, 启动命令 {' '.join(katana_command)}")

    try:
        subprocess.run(katana_command, check=True)  # 使用 run 在前台运行并等待其完成
        print("Katana 爬取完成。")

    except FileNotFoundError:
        return "错误: 'katana' 命令未找到。请确保 Katana 已安装并已添加到系统 PATH。"

    except subprocess.CalledProcessError as e:
        return f"Katana 运行时出错: {e}"

    except Exception as e:
        return f"运行 Katana 时发生未知错误: {e}"

    print("正在终止 Xray 进程...")
    xray_process.terminate()  # 确保 xray 进程被终止
    xray_process.wait()  # 等待进程完全终止
    print("Xray 进程已终止。")

    try:
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return "not found file or sempty"

        with open(file_path, "r", encoding="utf-8") as f:
            result = f.read()

        return result

    except Exception as e:
        return f"error: {str(e)}"


@mcp.tool()
async def katana_sqlmap(url: str) -> str:
    """使用 sqlmap 对目标进行 sql 漏洞扫描: 首先运行 katana 爬虫, 对目标 url 进行爬取, 然后使用 sqlmap 对爬取到的目标进行 sql 漏洞扫描

    Args:
        url (str): 目标 url, 比如: http://www.example.com

    Returns:
        str: 扫描到的漏洞数据
    """
    file_path = "./data/url.txt"
    command = ["katana", "-u", url, "-iqp", "-aff", "-fx", "-or", "-o", file_path]
    print(f"正在启动 Katana: {' '.join(command)}")

    try:
        subprocess.run(command, check=True)  # 使用 run 在前台运行并等待其完成
        print("Katana 爬取完成。")

    except FileNotFoundError:
        return "错误: 'katana' 命令未找到。请确保 Katana 已安装并已添加到系统 PATH。"

    except subprocess.CalledProcessError as e:
        return f"Katana 运行时出错: {e}"

    except Exception as e:
        return f"运行 Katana 时发生未知错误: {e}"

    cmd = ["sqlmap", "-m", file_path, "--batch"]
    print(f"正在启动 Sqlmap: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return str(e.stderr)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
    # mcp.run(transport="stdio")
