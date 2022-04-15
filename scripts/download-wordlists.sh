#!/usr/bin/env bash

mkdir -p wordlists
wget https://www.cs.cmu.edu/~biglou/resources/bad-words.txt -O wordlists/bad.txt
wget https://github.com/dwyl/english-words/raw/master/words_alpha.txt -O wordlists/english.txt
