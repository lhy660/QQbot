#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索工具（Playwright 版 · 仅百度）

命令行用法：
    python search_browser.py 搜索关键词
    python search_browser.py 搜索关键词 --count 5
    python search_browser.py 搜索关键词 --gui          # 弹出可见浏览器

作为模块调用（供集成到你自己的代码）：
    from search_browser import search, format_results, close_browser

    results = search("你的关键词")        # 返回列表，每项是 {"title", "url", "snippet"}
    web_message = format_results(results) # 整理成可读文本
    print(web_message)                    # 或把 web_message 交给你的主程序
    close_browser()                       # 用完后关闭浏览器

首次使用需安装：
    pip install playwright
    python -m playwright install chromium
"""

import argparse
import re
import sys
import urllib.parse

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # 未安装 playwright 时给出友好提示
    sync_playwright = None

BAIDU = "https://www.baidu.com/s"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


# ---------------------------------------------------------------- 浏览器层
_pw = None
_browser = None
_page = None


def _ensure_browser(headless=True):
    """启动（或复用）Chromium，返回 page。"""
    global _pw, _browser, _page
    if sync_playwright is None:
        raise RuntimeError(
            "未安装 playwright。请先执行：\n"
            "  pip install playwright\n"
            "  python -m playwright install chromium"
        )
    if _browser is None:
        _pw = sync_playwright().start()
        _browser = _pw.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        _page = _browser.new_page(user_agent=USER_AGENT)
    return _page


def close_browser():
    """关闭浏览器并释放资源。供调用方（main 程序）在搜索结束后调用。"""
    global _pw, _browser, _page
    try:
        if _browser:
            _browser.close()
    except Exception:
        pass
    try:
        if _pw:
            _pw.stop()
    except Exception:
        pass
    _pw = _browser = _page = None


# 兼容旧调用：保留下划线别名（内部使用）
_close_browser = close_browser


# ---------------------------------------------------------------- 提取脚本
_BAIDU_EXTRACT_JS = """
() => {
  const out = [];
  const seen = new Set();
  document.querySelectorAll('h3[class~="t"] a').forEach(a => {
    const title = (a.innerText || '').trim();
    const url = a.href || '';
    if (!title || seen.has(url)) return;
    seen.add(url);
    let snippet = '';
    const c = a.closest('.c-container, .result, .result-op');
    if (c) {
      const abs = c.querySelector('.c-abstract, [class*="content-right"]');
      if (abs) {
        snippet = (abs.innerText || '').trim();
      } else {
        snippet = (c.innerText || '').replace(title, '').trim();
      }
    }
    out.push({title, url, snippet});
  });
  return out;
}
"""


# ---------------------------------------------------------------- 文本清洗
def _clean_title(s):
    """标题：仅压缩空白。"""
    return re.sub(r"\s+", " ", s).strip()


def _clean_snippet(raw, limit=350):
    """清洗摘要：有句号取前 3 句；无标点(歌词/正文流)截前 80 字。"""
    raw = re.sub(r"\s+", " ", raw).strip()
    if not raw:
        return ""
    ends = [m.end() for m in re.finditer(r"[。！？!?；;]", raw)]
    if ends:
        target = min(3, len(ends))
        end = ends[target - 1]
        if end > limit and ends[0] <= limit:
            end = ends[0]
        elif end > limit:
            end = min(limit, len(raw))
        return raw[:end].strip()
    return (raw[:80] + "…") if len(raw) > 80 else raw


def _clean_results(raw):
    """清洗结果，并过滤验证页混入的标题。"""
    bad_titles = [
        "正在确认", "是不是机器人", "人机验证", "安全验证",
        "访问验证", "captcha", "verify you are", "before we continue",
    ]
    results = []
    for r in raw or []:
        title = _clean_title(r.get("title") or "")
        if not title:
            continue
        low = title.lower()
        if any(b in title or b.lower() in low for b in bad_titles):
            continue
        url = r.get("url") or ""
        snippet = _clean_snippet(r.get("snippet") or "")
        results.append({"title": title, "url": url, "snippet": snippet})
    return results


# ---------------------------------------------------------------- 搜索
def _search_baidu(query):
    page = _ensure_browser()
    url = BAIDU + "?" + urllib.parse.urlencode({"wd": query})
    page.goto(url, timeout=30000)
    try:
        # 安全验证页会自动 JS 跳转到结果页，这里等结果出现
        page.wait_for_selector('h3[class~="t"] a', timeout=15000)
    except Exception:
        title = ""
        try:
            title = page.title()
        except Exception:
            pass
        if "验证" in title or "安全" in title:
            raise RuntimeError(
                "百度触发了安全验证（可能需要人工滑块）。"
                "可加 --gui 参数弹出浏览器手动验证一次。"
            )
    return _clean_results(page.evaluate(_BAIDU_EXTRACT_JS))


def search(query, limit=10):
    """用百度搜索「query」（关键词），返回结果列表。

    每条结果是一个字典：{"title": 标题, "url": 链接, "snippet": 摘要}。
    """
    results = _search_baidu(query)
    return results[:limit]


# ---------------------------------------------------------------- 输出
def format_results(results):
    """把结果列表整理成可读文本，返回字符串（不打印）。

    供调用方（main 程序）拿到字符串后自行决定如何展示/转发。
    """
    if not results:
        return "（未找到结果）"
    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        lines.append(f"[{i}] {title}")
        if snippet:
            lines.append(f"    {snippet}")
    return "\n".join(lines)


def print_results(results):
    """在命令行直接打印结果（供独立运行时使用）。"""
    print("=" * 60)
    print(format_results(results))
    print("=" * 60)


# ---------------------------------------------------------------- 入口
def main():
    parser = argparse.ArgumentParser(description="搜索工具：输入关键词，输出搜索结果")
    parser.add_argument("query", nargs="*", help="搜索关键词")
    parser.add_argument("--count", type=int, default=10, help="显示结果条数（默认 10）")
    parser.add_argument("--gui", action="store_true", help="弹出可见浏览器窗口")
    args = parser.parse_args()

    query = " ".join(args.query).strip()
    if not query:
        query = input("请输入搜索内容：").strip()
    if not query:
        print("未输入搜索内容。")
        return

    try:
        _ensure_browser(headless=not args.gui)
    except Exception as e:
        print(f"⚠️ {e}")
        return

    try:
        results = search(query, limit=args.count)
        print_results(results)
    except Exception as e:
        print(f"⚠️ {e}")
    finally:
        close_browser()


if __name__ == "__main__":
    main()
