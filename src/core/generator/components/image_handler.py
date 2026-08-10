from PIL import Image, ImageChops
import hashlib
import os
from reportlab.platypus import Image as RLImage, Paragraph

from src.core.application.image_edit_compositor import render_edited_image
from src.core.domain.image_workspace import deserialize_annotation, deserialize_crop


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

            bg = Image.new(img.mode, img.size, img.getpixel((0, 0)))
            diff = ImageChops.difference(img, bg)
            bbox = diff.getbbox()

            if bbox:
                img = img.crop(bbox)

            img_final = Image.new("RGB", (largura_alvo, altura_alvo), (255, 255, 255))
            img.thumbnail((largura_alvo - 10, altura_alvo - 10), Image.Resampling.LANCZOS)

            x_offset = (largura_alvo - img.width) // 2
            y_offset = (altura_alvo - img.height) // 2

            img_final.paste(img, (x_offset, y_offset), img if img.mode == "RGBA" else None)

            os.makedirs("output_pdfs/temp", exist_ok=True)
            digest = hashlib.md5(os.path.abspath(caminho_imagem).encode("utf-8")).hexdigest()[:12]
            caminho_temp = f"output_pdfs/temp/peca_{digest}_{largura_alvo}x{altura_alvo}.png"
            img_final.save(caminho_temp, "PNG")

            return caminho_temp
        except Exception as e:
            print(f"[ReportImageHandler] Erro ao processar imagem: {e}")
            return caminho_imagem

    @classmethod
    def criar_elemento_foto(
        cls,
        caminho_imagem: str,
        styles: dict,
        *,
        largura: int = 180,
        altura: int = 105,
        preserve_original: bool = False,
        edits: dict | None = None,
    ):
        """Processa a imagem e retorna o elemento gráfico pronto para o ReportLab."""
        source_path = cls._resolve_source_path(caminho_imagem, edits)
        if preserve_original:
            elemento = cls._criar_elemento_foto_preservado(
                source_path,
                largura=largura,
                altura=altura,
            )
            if elemento is not None:
                return elemento

        caminho_tratado = cls.processar_foto_peca(
            source_path, largura_alvo=largura, altura_alvo=altura,
        )

        if caminho_tratado and os.path.exists(caminho_tratado):
            return RLImage(caminho_tratado, width=max(largura - 5, 1), height=max(altura - 5, 1))
        fallback_style = styles.get("celula_centro") or styles.get("texto")
        return Paragraph("<b>[ FOTO DA PEÇA ]</b>", fallback_style)

    @staticmethod
    def _resolve_source_path(caminho_imagem: str, edits: dict | None) -> str:
        if not edits:
            return caminho_imagem
        crop = deserialize_crop(edits.get("crop"))
        annotations = [
            item
            for item in (
                deserialize_annotation(entry)
                for entry in (edits.get("annotations") or [])
                if isinstance(entry, dict)
            )
            if item is not None
        ]
        if crop is None and not annotations:
            return caminho_imagem
        edited = render_edited_image(
            caminho_imagem,
            crop=crop,
            annotations=annotations,
        )
        return str(edited) if edited is not None else caminho_imagem

    @staticmethod
    def _criar_elemento_foto_preservado(
        caminho_imagem: str,
        *,
        largura: int,
        altura: int,
    ) -> RLImage | None:
        """Escala proporcionalmente sem recorte nem troca de fundo."""
        if not caminho_imagem or not os.path.exists(caminho_imagem):
            return None
        try:
            with Image.open(caminho_imagem) as img:
                img_w, img_h = img.size
            if img_w <= 0 or img_h <= 0:
                return None
            scale = min(largura / img_w, altura / img_h)
            draw_w = max(1, int(img_w * scale))
            draw_h = max(1, int(img_h * scale))
            return RLImage(caminho_imagem, width=draw_w, height=draw_h)
        except Exception as e:
            print(f"[ReportImageHandler] Erro ao preservar imagem: {e}")
            return None
