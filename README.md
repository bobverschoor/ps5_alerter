# ps5_alerter
Vanwege de enorme belangstelling voor de Playstation 5 een scriptje die bij diverse winkels de leverbaarheid controleert, en indien leverbaar deze status naar Telegram post.

Public channel Telegram: ps5-alerter-nl

# Install
git clone naar b.v. /home/pi

Via crontab -e: 
"* * * * * cd /home/pi/ps5_alerter;/usr/bin/python3 src/main/python/ps5_main.py >> ~/cron.log 2>&1"
    
Deze loopt nu elke minuut, en schrijft log in cron.log in je home dir