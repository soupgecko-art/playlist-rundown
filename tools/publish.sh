#!/bin/bash
# Publish every rundown MP3 in pod-runs/ to the Castbox feed.
# Usage: bash /mnt/project-files/podcast-feed/publish.sh   (add a title+summary for the new date to episodes.json first)
set -e
D=/mnt/project-files/podcast-feed; R=/home/user/playlist-rundown
[ -d $R/.git ] || git clone --depth 1 https://github.com/soupgecko-art/playlist-rundown $R
python3 $D/build_feed.py --base-url https://soupgecko-art.github.io/playlist-rundown
cp -r $D/site/. $R/ && cp $D/{build_feed.py,make_cover.py,episodes.json,publish.sh} $R/tools/
cd $R && git add -A && git -c user.name=Claude -c user.email=noreply@anthropic.com commit -qm "Update feed" && git -c push.negotiate=true push origin HEAD:main
