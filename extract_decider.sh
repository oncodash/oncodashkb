#!/usr/bin/bash

set -e

if [[ -z "$1" ]] ; then
    echo "Usage: $0 <data dir>" >&2
    exit 2
fi

cd $1

# "cnas_v2.9_short_mutations_v4.10.zip"
#blob:https://tt.eduuni.fi/cdea3f2a-3598-4815-813a-aa09cffe4e8e
unzip "cnas_v2.9_short_mutations_v4.10.zip"


# "12122025_Clinical export DECIDER collab.xlsx"
#https://tt.eduuni.fi/sites/hy-HautaniemiCollaboration/_layouts/15/download.aspx?SourceUrl=%2Fsites%2Fhy%2DHautaniemiCollaboration%2FShared%20Documents%2FDECIDER%2FDECIDER%20WP1%20Clinical%20data%2F12122025%5FClinical%20export%20DECIDER%20collab%2Exlsx

mkdir clinical
mv "12122025_Clinical export DECIDER collab.xlsx" clinical/12122025_Clinical_export_DECIDER_collab.xlsx


# actionable data
#blob:https://tt.eduuni.fi/e30baa0a-c332-4713-89fb-725166c307ae
mkdir placeholders
unzip OneDrive_1_20-04-2026.zip -d placeholders/


# vTMB.zip
#blob:https://tt.eduuni.fi/0cdb2983-6c24-4362-82a6-8a0fa23e7877
unzip vTMB.zip

