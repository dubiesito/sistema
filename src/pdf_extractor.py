import os
import re
from pdf2image import convert_from_path
import pytesseract
from PIL import ImageEnhance
from PySide6.QtCore import QDate

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
RUTA_POPPLER = os.path.join(TOOLS_DIR, "poppler", "Library", "bin")
RUTA_TESSERACT = os.path.join(TOOLS_DIR, "tesseract", "tesseract.exe")

pytesseract.pytesseract.tesseract_cmd = RUTA_TESSERACT

def extraer_datos_inteligentes_pdf(ruta_pdf):
    if not ruta_pdf or not os.path.exists(ruta_pdf):
        return None

    try:
        imagenes = convert_from_path(
            ruta_pdf, 
            first_page=1, 
            last_page=3, 
            poppler_path=RUTA_POPPLER
        )
        
        texto_suave_total = ""
        texto_fuerte_total = ""
        
        for img in imagenes:
            img_gris = img.convert('L')
            
            # 1. Lectura Suave (Fiel y limpia, evita alucinaciones de píxeles)
            texto_suave_total += pytesseract.image_to_string(img_gris, lang='spa') + " \n "
            
            # 2. Lectura Fuerte (Respaldo exclusivo para textos antiguos/pálidos)
            enhancer_fuerte = ImageEnhance.Contrast(img_gris)
            img_temp = enhancer_fuerte.enhance(2.0)
            enhancer_sharp = ImageEnhance.Sharpness(img_temp)
            img_fuerte = enhancer_sharp.enhance(2.0)
            texto_fuerte_total += pytesseract.image_to_string(img_fuerte, lang='spa') + " \n "
            
        limpio_suave = " ".join(texto_suave_total.split())
        limpio_fuerte = " ".join(texto_fuerte_total.split())

        # Función interna de extracción para aplicar a cualquier texto
        def extraer_campos(texto_cabecera, texto_completo):
            res, sigla, exp, ofi, fecha, tipo, titulo = None, None, None, None, None, None, None
            
            # 1. Resolución
            match_res = re.search(r'(AU|CU|R|VRAC|VRIN|CF|D)\s*-\s*([0-9oO\s]{1,4})\s*-\s*([0-9oO\s]{4})\s*-\s*UNSAAC', texto_cabecera, re.IGNORECASE)
            if match_res:
                res_sucia = match_res.group(0).upper()
                res = res_sucia.replace(" ", "").replace("O", "0")
                sigla = match_res.group(1).upper()

            # 2. Expediente
            match_exp = re.search(r'Expediente[^\d]*(\d{4,8})', texto_cabecera, re.IGNORECASE)
            if match_exp:
                exp = match_exp.group(1).zfill(8)

            # 3. Oficio
            match_ofi = re.search(r'Oficio[^\d]*(\d{3}\s*-\s*\d{4}\s*-\s*[A-Z]{1,4}\s*-\s*UNSAAC|\d{3}\s*-\s*[A-Z]{1,4}\s*[/-]\s*UNSAAC\s*-\s*\d{4})', texto_cabecera, re.IGNORECASE)
            if match_ofi:
                ofi = match_ofi.group(1).replace(" ", "").upper()

            # 4. Fecha
            meses = {
                "enero":1, "ene":1, "febrero":2, "feb":2, "marzo":3, "mar":3, 
                "abril":4, "abr":4, "mayo":5, "may":5, "junio":6, "jun":6, 
                "julio":7, "jul":7, "agosto":8, "ago":8, "setiembre":9, "septiembre":9, "sep":9, "set":9,
                "octubre":10, "oct":10, "noviembre":11, "nov":11, "diciembre":12, "dic":12
            }
            match_fecha = re.search(r'Cusco[\s\S]{0,40}?([0-9oO\s]{1,4})\s*(?:de\s*)?([a-zA-Z]{3,10})\.?\s*(?:de\s*)?([0-9oO\s]{4,6})', texto_completo, re.IGNORECASE)
            if match_fecha:
                try:
                    dia = int(match_fecha.group(1).upper().replace("O", "0").replace(" ", ""))
                    mes_str = match_fecha.group(2).lower()
                    anio = int(match_fecha.group(3).upper().replace("O", "0").replace(" ", ""))
                    if anio > 2100:
                        anio = int(str(anio)[:4])
                    mes = meses.get(mes_str, 1)
                    if dia > 31: dia = 31
                    fecha = QDate(anio, mes, dia)
                except:
                    pass

            # 5. Tipo y Título
            match_resuelve = re.search(r'RESUELVE[:;\.\s]+(.*?)(SEGUNDO|ART[ÍI]CULO|\Z)', texto_completo, re.IGNORECASE)
            texto_busq = match_resuelve.group(1) if match_resuelve else texto_completo
            
            tipos_posibles = ["Aprobar", "Acumular", "Crear", "Modificar", "Encargar", "Disponer", "Establecer", "Proponer", "Concluir"]
            for t in tipos_posibles:
                if t.upper() in texto_busq.upper() or (t == "Concluir" and "CONCLUIDO" in texto_busq.upper()):
                    tipo = t
                    break

            match_tit = re.search(r'(APROBAR|ACUMULAR|CREAR|MODIFICAR|ENCARGAR|DISPONER|ESTABLECER|PROPONER)\s+(?:LA\s+|EL\s+|LOS\s+|LAS\s+|AL\s+|DEL\s+)?(.*?)(?:,|aprobado|el\s+mismo)', texto_busq, re.IGNORECASE)
            if match_tit:
                titulo = " ".join(match_tit.group(2).strip().split()).upper()

            return res, sigla, exp, ofi, fecha, tipo, titulo

        # --- EJECUCIÓN EN CASCADA ---
        # Primero intentamos con la lectura suave (prioridad absoluta a la precisión)
        res, sigla, exp, ofi, fecha, tipo, titulo = extraer_campos(limpio_suave[:1500], limpio_suave)
        
        # Si la lectura suave dejó cabos sueltos, usamos la fuerte como respaldo
        if not res or not fecha:
            res_f, sig_f, exp_f, ofi_f, fec_f, tip_f, tit_f = extraer_campos(limpio_fuerte[:1500], limpio_fuerte)
            res = res or res_f
            sigla = sigla or sig_f
            exp = exp or exp_f
            ofi = ofi or ofi_f
            fecha = fecha or fec_f
            tipo = tipo or tip_f
            titulo = titulo or tit_f

        datos = {
            "resolucion": res or "",
            "sigla_organo": sigla or "",
            "expediente": exp or "",
            "oficio": ofi or "",
            "tipo": tipo or "",
            "titulo": titulo or "",
            "fecha": fecha
        }

        print(f"\n====== DATOS FINALES EXTRAÍDOS ======\n{datos}\n=====================================\n")
        return datos

    except Exception as e:
        print(f"Error crítico procesando el OCR: {e}")
        return None