create-zip:
	cd venv/lib/python3.8/site-packages && zip -r ${OLDPWD}/exchange_rate/function.zip . && cd ${OLDPWD}/exchange_rate && zip -g function.zip lambda_exchange_rate.py
