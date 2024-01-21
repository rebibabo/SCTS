lang=java
task=trans
scope=one
style='12.1'

cd ..
python transfer.py \
    --lang  ${lang} \
    --task  ${task} \
    --scope ${scope} \
    --style ${style}    
wait