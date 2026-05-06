# RSA Key Generation
Run these commands in the backend folder:

openssl genrsa -out keys/private.pem 2048
openssl rsa -in keys/private.pem -pubout -out keys/public.pem

NEVER commit private.pem to git!
