KEY=$(sed -n '1p' .env)
SECRET=$(sed -n '2p' .env)

export $KEY
export $SECRET

python shogun_web.py
