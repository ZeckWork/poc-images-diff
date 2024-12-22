import os
import requests
from PIL import Image
import time
import sys
import argparse
import subprocess

# Função para comprimir uma imagem e retornar o tamanho original, comprimido e redução percentual
def compress_image(image_path, quality=85):
    original_size = os.path.getsize(image_path)
    with Image.open(image_path) as img:
        img = img.convert("RGB")  # Converte para RGB para garantir compatibilidade
        img.save(image_path, quality=quality)  # Salva com a qualidade ajustada
    compressed_size = os.path.getsize(image_path)
    
    # Calcula a redução percentual
    reduction_percentage = 100 - (compressed_size * 100 / original_size)
    return original_size, compressed_size, reduction_percentage

# Função para comprimir todas as imagens em um diretório
def compress_images_in_directory(directory, quality=85, file_types=None):
    if file_types is None:
        file_types = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    compressed_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in file_types):
                image_path = os.path.join(root, file)
                original_size, compressed_size, reduction_percentage = compress_image(image_path, quality)
                compressed_files.append({
                    'file': image_path,
                    'original_size': original_size,
                    'compressed_size': compressed_size,
                    'reduction_percentage': reduction_percentage
                })
    return compressed_files

# Função para gerar o relatório
def generate_report(compressed_files):
    report = []
    for file_data in compressed_files:
        report.append(f"File: {file_data['file']}\n"
                      f"Original size: {file_data['original_size']} bytes\n"
                      f"Compressed size: {file_data['compressed_size']} bytes\n"
                      f"Reduction: {file_data['reduction_percentage']:.2f}%\n")
    return "\n".join(report)

# Função para comentar no PR no GitHub
def comment_on_pr(pr_number, comment, token, repo_owner, repo_name):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "body": comment
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print("Comment posted successfully.")
    else:
        print(f"Failed to post comment: {response.status_code}, {response.text}")

# Função para realizar commit e push no Git
def commit_and_push_changes(commit_message="Comprimir imagens e otimizar tamanhos"):
    # Garantir que estamos em uma branch válida
    subprocess.run(["git", "checkout", "-b", "compress-images-branch"], check=True)
    
    # Adiciona as mudanças no git
    subprocess.run(["git", "add", "."], check=True)
    
    # Faz o commit com a mensagem
    subprocess.run(["git", "commit", "-m", commit_message], check=True)
    
    # Envia as mudanças para o repositório remoto
    subprocess.run(["git", "push", "-u", "origin", "compress-images-branch"], check=True)

# Função principal
def main():
    # Argumentos de entrada via comando
    parser = argparse.ArgumentParser(description='Compress images and comment on PR.')
    parser.add_argument('--directory', type=str, default='.', help='Directory to search for images')
    parser.add_argument('--quality', type=int, default=85, help='Quality of compression (0-100)')
    parser.add_argument('--file_types', type=str, default='jpg,jpeg,png,gif,webp', help='Comma-separated list of file types to compress')
    parser.add_argument('--token', type=str, required=True, help='GitHub token')
    parser.add_argument('--repo_owner', type=str, required=True, help='GitHub repository owner')
    parser.add_argument('--repo_name', type=str, required=True, help='GitHub repository name')
    parser.add_argument('--pr_number', type=int, required=True, help='Pull Request number')
    
    args = parser.parse_args()

    file_types = args.file_types.split(',')

    print("Compressing images...")
    start_time = time.time()
    
    compressed_files = compress_images_in_directory(args.directory, args.quality, file_types)
    
    if compressed_files:
        print("Compression complete. Generating report...")
        report = generate_report(compressed_files)
        print(report)
        
        # Salvar o relatório em um arquivo
        with open("compression_report.txt", "w") as f:
            f.write(report)
        
        print(f"Report saved to 'compression_report.txt'")
        
        # Commit e Push das mudanças
        commit_and_push_changes()

        # Comentar no PR
        comment_on_pr(args.pr_number, report, args.token, args.repo_owner, args.repo_name)
    else:
        print("No image files found to compress.")
    
    end_time = time.time()
    print(f"Process completed in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()
