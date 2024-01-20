lang=c
task=trans
scope=one
style='7.2'

cd ..
python transfer.py \
    --lang  ${lang} \
    --task  ${task} \
    --scope ${scope} \
    --style ${style}    
wait