import requests
import base64
from docx2pdf import convert
import os



# 替换为您的百度API密钥和密钥
baidu_api_key = 'DejdpDlYntFdyzzFGeNqDDIJ'
baidu_secret_key = '3wzNVSx5ZeQYHXQTFQH4aZUBZDnvQPOV'

def get_baidu_access_token(api_key, secret_key):
    url = f'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}'
    response = requests.get(url)
    access_token = response.json()['access_token']
    return access_token

def recognize_text_with_baidu(image_path, pdf_file, api_key, secret_key):
    request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    all_text = []

    if image_path:
        with open(image_path, 'rb') as image_file:
            img_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        params = {
            'image': img_base64,
            'access_token': get_baidu_access_token(api_key, secret_key)
        }
        response = requests.post(request_url, data=params, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if 'words_result' in result:
                extracted_text = [item['words'] for item in result['words_result']]
                all_text.extend(extracted_text)
    elif pdf_file:
        with open(pdf_file, 'rb') as pdf_file_obj:
            pdf_base64 = base64.b64encode(pdf_file_obj.read()).decode('utf-8')
        
        # 先获取PDF总页数
        params = {
            'pdf_file': pdf_base64,
            'access_token': get_baidu_access_token(api_key, secret_key)
        }
        response = requests.post(request_url, data=params, headers=headers)
        if response.status_code == 200:
            result = response.json()
            total_pages = int(result.get('pdf_file_size', 1))
            
            # 循环处理每一页
            for page_num in range(1, total_pages + 1):
                params = {
                    'pdf_file': pdf_base64,
                    'pdf_file_num': str(page_num),
                    'access_token': get_baidu_access_token(api_key, secret_key)
                }
                response = requests.post(request_url, data=params, headers=headers)
                if response.status_code == 200:
                    result = response.json()
                    if 'words_result' in result:
                        extracted_text = [item['words'] for item in result['words_result']]
                        all_text.extend(['=== 第{}页 ==='.format(page_num)])
                        all_text.extend(extracted_text)
                        all_text.extend([''])  # 添加空行分隔每页内容
    
    return all_text if all_text else None

# 将.doc或.docx文件转换为PDF
def convert_to_pdf(input_path, output_path):
    """
    Convert a .doc or .docx file to PDF.

    Args:
        input_path (str): Path to the input .doc or .docx file.
        output_path (str): Path to the output PDF file.

    Returns:
        None
    """
    convert(input_path, output_path)


# 处理输入文件夹中的每个文件
def process_files(input_folder, output_folder):
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        if filename.lower().endswith('.pdf'):
            pdf_text = recognize_text_with_baidu(None, file_path, baidu_api_key, baidu_secret_key)
            content = '\n'.join(pdf_text) if pdf_text else ""
            save_text_to_file(output_folder, filename, content)
        elif filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            image_text = recognize_text_with_baidu(file_path, None, baidu_api_key, baidu_secret_key)
            content = '\n'.join(image_text) if image_text else ""
            save_text_to_file(output_folder, filename, content)
        elif filename.lower().endswith(('.doc', '.docx')):
            pdf_output_path = os.path.join(input_folder, f"{os.path.splitext(filename)[0]}.pdf")
            convert_to_pdf(file_path, pdf_output_path)  # Convert to PDF
            pdf_text = recognize_text_with_baidu(None, pdf_output_path, baidu_api_key, baidu_secret_key)
            content = '\n'.join(pdf_text) if pdf_text else ""
            save_text_to_file(output_folder, filename, content)
        else:
            continue

def save_text_to_file(output_folder, filename, content):
    output_file_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.txt")
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Extracted text from {filename} saved to {output_file_path}\n")

# 输入输出文件
input_folder = "input_path"
output_folder = "output_path"

# 如果输出文件夹不存在，则创建该文件夹
os.makedirs(output_folder, exist_ok=True)

# 使用百度OCR处理文件并提取文本，然后保存为文本文件
process_files(input_folder, output_folder)


