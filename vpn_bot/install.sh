#!/bin/bash
sudo apt update && sudo apt install -y python3 python3-pip git
pip3 install python-telegram-bot requests qrcode pillow

echo "دانلود پروژه..."
git clone https://github.com/EliteDevIR/vpn_sell_bot.git ~/vpn-bot
cd ~/vpn-bot
chmod +x install.sh

echo "شروع اجرای ربات..."
tmux new-session -d -s vpnbot "python3 main.py"
echo "نصب و اجرا انجام شد."
