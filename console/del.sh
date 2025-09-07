# Удалить проект
rm -rf /root/insales-telegram-shop
# После закачать проект на сервер, что все совпадало с github
# И перезагрузить порт либо все

# Затем pull
cd /root/insales-telegram-shop
git remote -v
git remote set-url origin git@github.com:Fis9000/4insales-telegram-shop.git
GIT_SSH_COMMAND='ssh -i ~/.ssh/insales-telegram-shop_github_deploy_key' git pull




# Удалить все что в проекте
rm -rf /root/services/insales-telegram-shop/{*,.*} 2>/dev/null

