#!/bin/bash

printf 'Script called: "%s" "%s"\n' "$1" "$2" >> /home/torrent/strauto/echo_path.log ;

if [ "$2" == "testing" ] 
    then
        printf '%s\n' "$1" >> /home/torrent/strauto/strautoreport
fi
