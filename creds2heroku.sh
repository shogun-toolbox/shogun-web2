KEY=$(sed -n '1p' .env)
SECRET=$(sed -n '2p' .env)

heroku config:set $KEY
heroku config:set $SECRET
