BODY='{}'
TIMESTAMP=$(date +%s)
SECRET="FAKE_DEV_SECRET_NOT_SECURE!!!!!!"
SIGNATURE=$(echo -n "$TIMESTAMP$BODY" | openssl dgst -sha256 -hmac "$SECRET" | cut -d " " -f2)
curl -X POST http://127.0.0.1:5000/deploy_email_sender \
     -H "Content-Type: application/json" \
     -H "X-Timestamp: $TIMESTAMP" \
     -H "X-Signature: $SIGNATURE" \
     -d "$BODY"
