#!/bin/bash
echo 'make api-urls.json'
django-admin show_urls --settings=settings.production | grep -v "<format>" | awk 'BEGIN{print "{"} NR > 1 { print "," } { printf("\"%s\": \"%s\"", $3, $1)} END{ print "\n}"}' | column -t > src/javascript/api-urls.json
