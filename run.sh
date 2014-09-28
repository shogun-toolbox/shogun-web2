cat .env | while read line
do
  export $line
done

python shogun_web.py
