lang=java
task=trans
scope=one
style='11.2'

cd ..
python transfer.py \
    --lang  ${lang} \
    --task  ${task} \
    --scope ${scope} \
    --style ${style}    
wait