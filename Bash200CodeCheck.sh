#!/bin/bash

input_file="<FILE OF URLs TO SCAN>"
output_file="<OUTPUT OF SCAN>"

# Check if input file exists
if [ ! -f "$input_file" ]; then
    echo "Input file $input_file not found!"
    exit 1
fi

# Clear the output file if it already exists
> "$output_file"

# Read URLs from the input file and process them with httpx
while IFS= read -r url
do
    echo "Processing: $url"
    httpx "$url" --follow-redirects -v >> "$output_file"
    echo -e "\n---\n" >> "$output_file"  # Add a separator between results
done < "$input_file"

echo "Processing complete. Results saved in $output_file"
