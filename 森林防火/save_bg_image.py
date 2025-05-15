import os
import shutil
import base64
from PIL import Image
import io

def save_example_bg():
    """创建一个默认背景图示例"""
    
    # 确保目标目录存在
    target_dir = os.path.join('static', 'img')
    os.makedirs(target_dir, exist_ok=True)
    
    # 目标文件路径
    target_path = os.path.join(target_dir, 'forest_bg.jpg')
    
    # 检查文件是否已存在
    if os.path.exists(target_path):
        print(f"背景图片已存在: {target_path}")
        return
    
    # 在这里添加默认图片的base64编码数据，或者从其他位置复制图片
    print(f"请将您的森林守护者背景图片重命名为 'forest_bg.jpg' 并放置在 {target_dir} 目录下")
    print("然后重新启动应用以查看更改")

if __name__ == "__main__":
    save_example_bg() 