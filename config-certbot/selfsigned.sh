path=/etc/letsencrypt/live/${MN_HOSTNAME}
rsa_key_size=4096

##
# Create self-signed certificate if file does not exist
if [ ! -f "$path/fullchain.pem" ]; then
    echo "### Creating self-signed certificate for $MN_HOSTNAME ..."
    echo "$path/conf/live/$MN_HOSTNAME"
    mkdir -p $path
    openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 3650\
        -keyout $path/privkey.pem \
        -out $path/fullchain.pem \
        -subj "/CN=${MN_HOSTNAME}"
    touch $path/SELF_SIGNED
fi