# Ensure all subdomains are live and responsive
for url in $(cat updated_subdomains.txt); do
    echo "Testing $url"
    status_code=$(curl -o /dev/null --silent --head --write-out '%{http_code}' "https://$url")
    echo "$url: HTTP Status Code = $status_code"
    if [ "$status_code" == "200" ] || [ "$status_code" == "301" ]; then
        echo "Active: $url" >> active_subdomains.txt
    else
        echo "Inactive: $url" >> inactive_subdomains.txt
    fi
done
