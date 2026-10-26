#!/usr/bin/env bash
# ============================================================
#  QQ 机器人启动器
#  菜单：1 启动主程序 / 2 安装依赖 / 3 配置账号与Key / 4 退出
# ============================================================

CONF_DIR="$HOME/qqbotenv"                 # 虚拟环境 & 配置文件目录
CONF_FILE="$CONF_DIR/qqbot.conf"          # 存放 QQID / AIKEY
VENV_ACTIVATE="$CONF_DIR/bin/activate"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

C_RESET='\033[0m'; C_CYAN='\033[36m'; C_GREEN='\033[32m'
C_YELLOW='\033[33m'; C_RED='\033[31m'

# ---------- 配置读写 ----------
load_conf() {
    QQID=""; AIKEY=""
    if [[ -f "$CONF_FILE" ]]; then
        # shellcheck source=/dev/null
        source "$CONF_FILE" 2>/dev/null || true
    fi
}

# 单引号安全转义： abc'def -> 'abc'\''def'
sq_escape() { printf "%s" "$1" | sed "s/'/'\\\\''/g"; }

save_conf() {
    mkdir -p "$CONF_DIR"
    {
        printf "QQID='%s'\n"  "$(sq_escape "$QQID")"
        printf "AIKEY='%s'\n" "$(sq_escape "$AIKEY")"
    } > "$CONF_FILE"
    chmod 600 "$CONF_FILE"
    echo -e "${C_GREEN}配置已写入：$CONF_FILE${C_RESET}"
}

mask_key() {   # 脱敏显示
    local k="$1" n
    n=${#k}
    if   (( n == 0 )); then echo "(未设置)"
    elif (( n <= 8 )); then echo "${k:0:2}******"
    else echo "${k:0:4}****${k: -4}"
    fi
}

# ---------- 选项 3：设定 / 重置 ----------
set_account() {
    load_conf
    echo -e "${C_CYAN}—— 设定机器人账号与 API-Key ——${C_RESET}"
    echo -e "当前 QQID   ：${C_YELLOW}$QQID${C_RESET}"
    echo -e "当前 API-Key：${C_YELLOW}$(mask_key "$AIKEY")${C_RESET}"
    echo "（直接回车表示保留原值，输入新值则覆盖）"
    echo

    local in_id in_key
    read -r -p "请输入机器人 QQ 号 [${QQID}]: " in_id
    [[ -n "$in_id" ]] && QQID="$in_id"

    read -r -s -p "请输入 API-Key（输入内容不回显，回车保留原值）: " in_key
    echo
    [[ -n "$in_key" ]] && AIKEY="$in_key"

    save_conf
}

# ---------- 选项 1：启动主程序 ----------
start_bot() {
    load_conf

    if [[ ! -f "$VENV_ACTIVATE" ]]; then
        echo -e "${C_RED}未找到虚拟环境：$CONF_DIR${C_RESET}"
        echo -e "请先选择 ${C_YELLOW}2${C_RESET} 安装依赖环境。"
        return 0
    fi
    if [[ -z "$QQID" || -z "$AIKEY" ]]; then
        echo -e "${C_RED}QQID 或 API-Key 为空，请先在选项 3 中设置。${C_RESET}"
        return 0
    fi

    local app="$SCRIPT_DIR/aichat.py"
    [[ -f "$app" ]] || app="$HOME/aichat.py"
    if [[ ! -f "$app" ]]; then
        echo -e "${C_RED}找不到 aichat.py（已查找：$SCRIPT_DIR 与 $HOME）${C_RESET}"
        return 0
    fi

    echo -e "${C_CYAN}启动机器人主程序...${C_RESET}"
    # shellcheck source=/dev/null
    source "$VENV_ACTIVATE"
    export AIKEY="$AIKEY"
    export QQID="$QQID"
    cd "$(dirname "$app")" || return 1
    python3 aichat.py
    local rc=$?
    deactivate 2>/dev/null || true
    echo
    if (( rc == 0 )); then
        echo -e "${C_GREEN}主程序已退出。${C_RESET}"
    else
        echo -e "${C_YELLOW}主程序以退出码 $rc 结束。${C_RESET}"
    fi
}

# ---------- 选项 2：安装依赖 ----------
install_deps() {
    echo -e "${C_CYAN}—— 安装依赖环境 ——${C_RESET}"
    sudo apt update || { echo -e "${C_RED}apt update 失败${C_RESET}"; return 0; }
    sudo apt install -y python3 python3-pip python3-venv || {
        echo -e "${C_RED}依赖安装失败${C_RESET}"; return 0; }

    cd "$HOME" || return 1
    if [[ ! -f "$VENV_ACTIVATE" ]]; then
        python3 -m venv "$CONF_DIR" || { echo -e "${C_RED}虚拟环境创建失败${C_RESET}"; return 0; }
    else
        echo -e "${C_GREEN}虚拟环境已存在，跳过创建。${C_RESET}"
    fi

    # shellcheck source=/dev/null
    source "$VENV_ACTIVATE"

    echo -e "正在通过清华镜像源安装 Python 依赖..."
    if pip install flask requests openai \
            -i https://pypi.tuna.tsinghua.edu.cn/simple; then
        pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
        pip cache purge 2>/dev/null || true
        echo -e "${C_GREEN}依赖安装完成，已清理 pip 下载缓存。${C_RESET}"
    else
        echo -e "${C_RED}依赖安装失败，请检查网络或镜像源后重试。${C_RESET}"
    fi

    deactivate 2>/dev/null || true
    cd "$SCRIPT_DIR" || true
}

# ---------- 菜单 ----------
show_menu() {
    load_conf
    clear
    echo -e "${C_CYAN}============================================${C_RESET}"
    echo -e "${C_CYAN}           QQ 机器人启动器${C_RESET}"
    echo -e "${C_CYAN}============================================${C_RESET}"
    echo -e "  QQ机器人账号：${C_YELLOW}${QQID:-(未设置)}${C_RESET}"
    echo -e "  DeepseekAPI_Key ：${C_YELLOW}$(mask_key "$AIKEY")${C_RESET}"
    echo -e "  虚拟环境：$([ -f "$VENV_ACTIVATE" ] && echo -e "${C_GREEN}已就绪${C_RESET}" || echo -e "${C_RED}未安装${C_RESET}")"
    echo -e "${C_CYAN}--------------------------------------------${C_RESET}"
    echo "  1) 启动机器人主程序"
    echo "  2) 安装依赖环境"
    echo "  3) 设定 API-Key / 机器人账号（可重置）"
    echo "  4) 退出"
    echo -e "${C_CYAN}============================================${C_RESET}"
}

main() {
    while true; do
        show_menu
        read -r -p "请选择 [1-4]: " choice || exit 0
        case "$choice" in
            1) start_bot; read -r -p "按回车返回菜单..." _ || exit 0 ;;
            2) install_deps; read -r -p "按回车返回菜单..." _ || exit 0 ;;
            3) set_account;  read -r -p "按回车返回菜单..." _ || exit 0 ;;
            4) echo -e "${C_GREEN}再见！${C_RESET}"; exit 0 ;;
            *) echo -e "${C_RED}无效选择，请输入 1-4${C_RESET}"; sleep 1 ;;
        esac
    done
}

main "$@"
