#!/usr/bin/env bash

mkdir -p wordlists
if [ ! -f wordlists/bad.txt ]
then
    wget https://www.cs.cmu.edu/~biglou/resources/bad-words.txt -O wordlists/bad.txt
fi
if [ ! -f wordlists/english.txt ]
then
    wget https://github.com/dwyl/english-words/raw/master/words_alpha.txt -O wordlists/english.txt
fi
