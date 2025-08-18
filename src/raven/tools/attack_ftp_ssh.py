import asyncio
from ftplib import FTP
import os
import subprocess
from typing import List, Literal, Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("FTP_SSH")


@mcp.tool()
async def brute_force_hydra(target: str, username: str, password_list_path: Optional[str] = None, ssh_options: Optional[List[str]] = None) -> str:
    """
    Perform an SSH brute-force attack on the target.
    Users need to pass in the target (IP or domain) and username. Optionally, they can provide the path to a password list file and additional SSH options.

    :param target: Target IP address or domain name.
    :param username: Username for SSH login.
    :param password_list_path: Path to the password list file. Defaults to None.
    :param ssh_options: Additional SSH command options. Defaults to None.
    """
    if ssh_options is None:
        ssh_options = [""]
    if password_list_path is None:
        password_list_path = "passwords.txt"

    cmd = "hydra -l " + username + " -P " + password_list_path + " " + target + " ssh " + " ".join(ssh_options)
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return str(e.stderr)


@mcp.tool()
async def anonymous_login(target: str, method: Literal["auto", "nmap", "python", "ftp"] = "auto") -> str:
    """
    检测 FTP 服务是否允许匿名登录（Anonymous Access）。
    支持四种检测方式：'nmap'、'python'、'ftp'、或 'auto'（默认顺序尝试）。

    ===========================
    ✅ 使用示例:
    ---------------------------
    ftp_anon_check(target="192.168.1.100", method="auto")
    ftp_anon_check(target="example.com", method="ftp")

    ===========================
    ✅ 参数说明:
    ---------------------------
    target (str): 目标 IP 或主机名
    method (str): 检测方式，可选项如下：
        - "auto": 默认顺序尝试 nmap → python → ftp
        - "nmap": 使用 Nmap ftp-anon 脚本
        - "python": 使用 ftplib 模块连接测试
        - "ftp": 使用 Linux 自带 ftp 命令行进行交互模拟（匿名登录）

    ===========================
    ✅ 返回说明:
    ---------------------------
    - 成功登录：显示欢迎信息 / 列表内容 / nmap 脚本输出
    - 登录失败：提示未授权或连接错误
    - 默认返回标准输出字符串，供大模型读取分析
    """
    if method == "nmap" or method == "auto":
        try:
            cmd = ["nmap", "-p", "21", "--script", "ftp-anon", target]
            process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
            stdout_bytes, _ = await process.communicate()
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            if "Anonymous FTP login allowed" in stdout:
                return f"✅ FTP Anonymous login allowed via Nmap\n\n{stdout}"
            elif method == "nmap":
                return f"❌ FTP Anonymous login NOT allowed (Nmap)\n\n{stdout}"
        except Exception as e:
            if method == "nmap":
                return f"❌ Nmap execution failed: {str(e)}"

    if method == "python" or method == "auto":
        try:
            ftp = FTP()
            ftp.connect(host=target, port=21, timeout=5)
            ftp.login(user="anonymous", passwd="")
            welcome = ftp.getwelcome()
            files = ftp.nlst()
            ftp.quit()
            return f"✅ FTP Anonymous login allowed via Python\n\nWelcome Message:\n{welcome}\n\nFiles:\n" + "\n".join(files)
        except Exception as e:
            if method == "python":
                return f"❌ FTP Anonymous login NOT allowed (Python): {str(e)}"

    if method == "ftp" or method == "auto":
        try:
            script = f"open {target}\nanonymous\n\nquit\n"
            process = await asyncio.create_subprocess_exec(
                "ftp", "-inv", stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
            )
            stdout_bytes, _ = await process.communicate(input=script.encode())
            stdout = stdout_bytes.decode("utf-8", errors="replace")

            if "230" in stdout:
                return f"✅ FTP Anonymous login allowed via ftp shell\n\n{stdout}"
            else:
                return f"❌ FTP Anonymous login NOT allowed via ftp shell\n\n{stdout}"

        except Exception as e:
            return f"❌ ftp shell execution failed: {str(e)}"

    return "❌ Unknown method. Use one of: auto, nmap, python, ftp"


@mcp.tool()
async def ftp_file_upload(
    target: str, test_filename: Optional[str] = "upload_test.txt", content: Optional[str] = "This is a test upload.", cleanup: bool = True
) -> str:
    """
    检测 FTP 服务器是否允许匿名用户上传文件（文件上传漏洞）。

    ===========================
    ✅ 示例用法:
    ---------------------------
    ftp_file_upload(target="192.168.1.100")
    ftp_file_upload(target="192.168.1.100", test_filename="test.php", content="<?php phpinfo();?>")

    ===========================
    ✅ 参数说明:
    ---------------------------
    target (str): 目标 FTP 服务器 IP 或域名
    test_filename (str, 可选): 要上传的测试文件名（默认: upload_test.txt）
    content (str, 可选): 文件内容（默认: 文本）
    cleanup (bool): 是否在测试后自动删除该文件（默认: True）

    ===========================
    ✅ 返回值说明:
    ---------------------------
    - 若允许上传，将返回 ✅ 并附加上传成功日志
    - 若失败，将返回 ❌ 和错误信息
    """
    if test_filename is None or content is None:
        return "❌ 无效的 test_filename 或 content 参数"
    try:
        ftp = FTP()
        ftp.connect(target, port=21, timeout=5)
        ftp.login(user="anonymous", passwd="")
        cwd = ftp.pwd()

        # 创建本地临时测试文件

        with open(test_filename, "w") as f:
            f.write(content)

        with open(test_filename, "rb") as f:
            ftp.storbinary(f"STOR {test_filename}", f)

        # 检查是否成功上传
        file_list = ftp.nlst()
        uploaded = test_filename in file_list

        # 清理上传文件
        if cleanup and uploaded:
            ftp.delete(test_filename)

        ftp.quit()
        if os.path.exists(test_filename):
            os.remove(test_filename)

        if uploaded:
            return (
                f"✅ FTP allows anonymous file upload!\n"
                f"Target: {target}\n"
                f"Uploaded file: {test_filename}\n"
                f"Upload directory: {cwd}\n"
                f"File auto-deleted: {cleanup}"
            )
        else:
            return "❌ Upload attempt made, but file not found after upload."

    except Exception as e:
        try:
            os.remove(test_filename)
        except Exception:
            pass
        return f"❌ FTP upload test failed: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
