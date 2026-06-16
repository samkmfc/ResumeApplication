"""PyCharm 一键运行入口。

直接在 PyCharm 里右键运行本文件即可启动后端（等价于
`uvicorn app.main:app --reload --port 8000`）。

注意：不要直接运行 app/main.py —— 它使用相对导入，作为脚本运行会报错。
本文件位于 backend 根目录，能正确把 app 当作包导入。
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
