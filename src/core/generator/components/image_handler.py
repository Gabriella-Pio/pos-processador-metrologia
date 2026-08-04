from PIL import Image, ImageChops
import os
from reportlab.platypus import Image as RLImage, Paragraph

class ReportImageHandler:
    @staticmethod
    def processar_foto_peca(caminho_imagem: str, largura_alvo: int = 180, altura_alvo: int = 105) -> str:
        """
        Realiza o tratamento automático da imagem:
        1. Auto-Crop (remove margens brancas ou vazias em excesso)
        2. Redimensionamento proporcional (Fit)
        3. Centralização exata em um fundo padronizado para o ReportLab.
        """
        if not caminho_imagem or not os.path.exists(caminho_imagem):
            return None

        try:
            img = Image.open(caminho_imagem).convert("RGBA")
            
            # 1. Auto-Crop: Remove espaços vazios baseado na cor do canto superior esquerdo
            bg = Image.new(img.mode, img.size, img.getpixel((0, 0)))
            diff = ImageChops.difference(img, bg)
            bbox = diff.getbbox()
            
            if bbox:
                img = img.crop(bbox)

            # 2. Tela de fundo padronizada com o tamanho exato da célula do PDF
            img_final = Image.new("RGB", (largura_alvo, altura_alvo), (255, 255, 255))
            
            # Redimensiona mantendo a proporção (Aspect Ratio)
            img.thumbnail((largura_alvo - 10, altura_alvo - 10), Image.Resampling.LANCZOS)
            
            # 3. Centralização automática
            x_offset = (largura_alvo - img.width) // 2
            y_offset = (altura_alvo - img.height) // 2
            
            img_final.paste(img, (x_offset, y_offset), img if img.mode == 'RGBA' else None)
            
            # Salva na pasta temporária para o ReportLab renderizar
            os.makedirs("output_pdfs/temp", exist_ok=True)
            caminho_temp = "output_pdfs/temp/peca_processada_temp.png"
            img_final.save(caminho_temp, "PNG")
            
            return caminho_temp
        except Exception as e:
            print(f"[ReportImageHandler] Erro ao processar imagem: {e}")
            return caminho_imagem

    @classmethod
    def criar_elemento_foto(cls, caminho_imagem: str, styles: dict):
        """
        Processa a imagem e retorna o elemento gráfico pronto para o ReportLab (RLImage)
        ou um Paragraph de fallback se não houver foto.
        """
        caminho_tratado = cls.processar_foto_peca(caminho_imagem, largura_alvo=180, altura_alvo=105)
        
        if caminho_tratado and os.path.exists(caminho_tratado):
            # Retorna a imagem redimensionada e dimensionada perfeitamente ao slot da tabela
            return RLImage(caminho_tratado, width=175, height=100)
        else:
            return Paragraph("<b>[ FOTO DA PEÇA ]</b>", styles['celula_centro'])