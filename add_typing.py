import re
import os

languages = ["c", "cpp", "java", "python"]

for language in languages:
    for file in os.listdir(language):
        if file.startswith("transform"):
            with open(os.path.join(language, file), "r", encoding='utf-8') as f:
                code = f.read()
                matches = re.findall(r'\b(def\s+)(rec_|match_)([\w_]*)(\s*\([^)]*\)\s*:)', code)
                for match in matches:
                    ori_line = ''.join(match)
                    s_ = ori_line.split(":")
                    line = s_[0] + " -> bool:" + s_[1]   
                    s_ = line.split("node")
                    line = s_[0] + "node: Node" + s_[1]
                    code = code.replace(ori_line, line)
                    
                matches = re.findall(r'\b(def\s+)(cvt)([\w_]*)(\s*\([^)]*\)\s*:)', code)
                for match in matches:
                    ori_line = ''.join(match)
                    s_ = ori_line.split(":")
                    line = s_[0] + " -> List[Tuple[int, Union[int, str]]]:" + s_[1]   
                    if 'code' in line:
                        s_ = line.split("code")
                        line = s_[0] + "code: str" + s_[1]
                    s_ = line.split("node")
                    line = s_[0] + "node: Node" + s_[1]
                    code = code.replace(ori_line, line)
                
            with open(os.path.join(language, file), "w", encoding='utf-8') as f:
                f.write(code)
            