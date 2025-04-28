#!/bin/bash

path=/etc/letsencrypt/live/${MN_HOSTNAME}
rsa_key_size=4096

if [ "$MN_USE_LETSENCRYPT" == "1" ]; then
    
    if [ -f "$path/SELF_SIGNED" ]; then
        rm -f $path/SELF_SIGNED $path/privkey.pem $path/fullchain.pem
        certbot certonly --webroot -w /var/www/certbot \
            --register-unsafely-without-email \
            -d $MN_HOSTNAME \
            --rsa-key-size $rsa_key_size \
            --agree-tos \
            --force-renewal
    fi

    trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;
fi