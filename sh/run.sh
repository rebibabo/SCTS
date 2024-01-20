lang=java
task=trans
scope=one
style='6.1'

cd ..
python transfer.py \
    --lang  ${lang} \
    --task  ${task} \
    --scope ${scope} \
    --style ${style}    
wait