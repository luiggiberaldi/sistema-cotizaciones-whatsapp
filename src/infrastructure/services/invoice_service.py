import os
from datetime import datetime
from fpdf import FPDF
from typing import Dict, List, Optional
from pathlib import Path
import requests
import tempfile
import shutil

class InvoiceService:
    """
    Servicio para generar PDFs de cotizaciones/facturas.
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        # En producción (Paas como Render), usualmente solo /tmp es escribible
        # Ensure we use a writable directory
        if output_dir is None:
            if os.name == 'nt':  # Windows local
                self.output_dir = "temp_pdfs"
            else:  # Linux/Unix (Render/Production)
                self.output_dir = "/tmp/temp_pdfs"
        else:
            self.output_dir = output_dir
            
        os.makedirs(self.output_dir, exist_ok=True)

    def _clean_text(self, text: str) -> str:
        """
        Limpia el texto para asegurar compatibilidad con la fuente estándar de FPDF (Latin-1).
        Reemplaza caracteres no soportados para evitar errores de codificación.
        """
        if not text:
            return ""
        # Codificar a latin-1 reemplazando errores, luego decodificar para tener string compatible
        return text.encode('latin-1', 'replace').decode('latin-1')

    def _download_image(self, url: str) -> Optional[str]:
        """
        Descarga una imagen temporalmente para insertarla en el PDF.
        Retorna la ruta del archivo temporal o None si falla.
        """
        if not url:
            return None
        try:
            response = requests.get(url, stream=True, timeout=5)
            if response.status_code == 200:
                # Crear archivo temporal
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                with open(temp_file.name, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)
                return temp_file.name
        except Exception as e:
            print(f"Error descargando imagen {url}: {e}")
            return None
        return None

    def generate_invoice_pdf(self, quote_data: Dict) -> str:
        """
        Genera un PDF para una cotización.
        
        Args:
            quote_data: Diccionario con los datos de la cotización (id, client_phone, items, total).
            
        Returns:
            Ruta del archivo PDF generado.
        """
        quote_id = quote_data.get('id', 'N/A')
        client_phone = quote_data.get('client_phone', 'N/A')
        items = quote_data.get('items', [])
        total = quote_data.get('total', 0.0)
        date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        pdf = FPDF()
        pdf.add_page()
        
        # --- Cabecera ---
        # Logo placeholder (un rectángulo azul con texto)
        pdf.set_fill_color(0, 102, 204)
        pdf.rect(10, 10, 40, 20, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 10)
        pdf.set_xy(10, 10)
        pdf.cell(40, 20, "LOGO EMPRESA", align='C')
        
        # Información de la empresa (derecha)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", 'B', 16)
        pdf.set_xy(60, 10)
        pdf.cell(0, 10, self._clean_text("COTIZACIÓN COMERCIAL"), ln=True, align='R')
        
        pdf.set_font("Arial", '', 10)
        pdf.set_xy(60, 20)
        pdf.cell(0, 5, f"No. Correlativo: {quote_id}", ln=True, align='R')
        pdf.cell(0, 5, f"Fecha: {date_str}", ln=True, align='R')
        
        pdf.ln(15)
        
        # --- Datos del Cliente ---
        client_name = quote_data.get('client_name') or 'N/A'
        client_dni = quote_data.get('client_dni') or 'N/A'
        client_address = quote_data.get('client_address') or 'N/A'
        
        # Limpiar textos de usuario para evitar errores de encoding
        client_name = self._clean_text(client_name)
        client_dni = self._clean_text(client_dni)
        client_address = self._clean_text(client_address)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, self._clean_text("Datos del Cliente"), ln=True)
        
        pdf.set_font("Arial", '', 11)
        pdf.cell(30, 6, "Cliente:", 0, 0)
        pdf.cell(0, 6, client_name, ln=True)
        
        pdf.cell(30, 6, "CI/RIF:", 0, 0)
        pdf.cell(0, 6, client_dni, ln=True)
        
        pdf.cell(30, 6, self._clean_text("Teléfono:"), 0, 0)
        pdf.cell(0, 6, client_phone, ln=True)
        
        pdf.cell(30, 6, self._clean_text("Dirección:"), 0, 0)
        pdf.multi_cell(0, 6, client_address)
        
        pdf.ln(5)
        
        # --- Tabla de Items ---
        # Cabecera de tabla
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(90, 10, "Producto", 1, 0, 'C', True)
        pdf.cell(30, 10, "Cantidad", 1, 0, 'C', True)
        pdf.cell(35, 10, "Precio Unit.", 1, 0, 'C', True)
        pdf.cell(35, 10, "Subtotal", 1, 1, 'C', True)
        
        # Items
        pdf.set_font("Arial", '', 10)
        row_height = 15  # Aumentamos altura para la imagen
        image_size = 12
        
        for item in items:
            product_name = self._clean_text(item.get('product_name', 'N/A'))
            image_url = item.get('image_url')
            
            # Guardamos posición Y actual
            y_start = pdf.get_y()
            x_start = pdf.get_x()
            
            # --- Celda Producto (con imagen) ---
            # Dibujamos el borde de la celda producto primero
            pdf.cell(90, row_height, "", 1)
            
            # Intentar poner imagen
            img_path = self._download_image(image_url) if image_url else None
            if img_path:
                try:
                    # Imagen a la izquierda con padding
                    pdf.image(img_path, x=x_start + 2, y=y_start + 1.5, w=image_size, h=image_size)
                    # Texto desplazado
                    pdf.set_xy(x_start + image_size + 4, y_start)
                    # Usamos MultiCell por si el nombre es largo, centrado verticalmente aprox
                    pdf.cell(90 - image_size - 4, row_height, product_name, 0, 0, 'L')
                    # Eliminar temp file
                    os.unlink(img_path)
                except Exception as e:
                    print(f"Error insertando imagen en PDF: {e}")
                    pdf.set_xy(x_start + 2, y_start)
                    pdf.cell(88, row_height, product_name, 0, 0, 'L')
            else:
                # Sin imagen, texto normal
                pdf.set_xy(x_start + 2, y_start)
                pdf.cell(88, row_height, product_name, 0, 0, 'L')
                
            # Volver a posición tras celda producto para las siguientes celdas
            pdf.set_xy(x_start + 90, y_start)
            
            pdf.cell(30, row_height, str(item.get('quantity', 0)), 1, 0, 'C')
            pdf.cell(35, row_height, f"${item.get('unit_price', 0):.2f}", 1, 0, 'R')
            pdf.cell(35, row_height, f"${item.get('subtotal', 0):.2f}", 1, 1, 'R')
            
        # --- Total ---
        pdf.ln(2)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(155, 10, "TOTAL:", 0, 0, 'R')
        pdf.set_fill_color(0, 102, 204)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(35, 10, f"${total:.2f}", 1, 1, 'R', True)
        
        # --- Footer ---
        pdf.set_text_color(100, 100, 100)
        pdf.set_font("Arial", 'I', 8)
        pdf.set_y(-30)
        pdf.cell(0, 10, self._clean_text("Gracias por preferirnos. Esta es una cotización generada automáticamente."), align='C')
        
        # Guardar archivo
        file_name = f"quote_{quote_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        file_path = os.path.join(self.output_dir, file_name)
        pdf.output(file_path)
        
        return os.path.abspath(file_path)

    def generate_catalog_pdf(self, products: List[Dict]) -> str:
        """
        Genera un catálogo de productos en PDF.
        """
        pdf = FPDF()
        pdf.add_page()
        
        # --- Cabecera ---
        pdf.set_fill_color(0, 102, 204)
        pdf.rect(0, 0, 210, 40, 'F')
        
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 24)
        pdf.set_xy(10, 10)
        pdf.cell(0, 15, "CATÁLOGO DE PRODUCTOS", ln=True, align='C')
        
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Actualizado: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
        
        pdf.set_xy(10, 45)
        pdf.set_text_color(0, 0, 0)
        
        # --- Tabla de Productos ---
        # Cabecera
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(100, 10, "Producto", 1, 0, 'L', True)
        pdf.cell(50, 10, "Categoría", 1, 0, 'C', True)
        pdf.cell(40, 10, "Precio", 1, 1, 'R', True)
        
        # Contenido
        pdf.set_font("Arial", '', 10)
        row_height = 18 # Altura fila
        image_size = 15 # Tamaño imagen
        
        for product in products:
            name = self._clean_text(product.get('name', 'N/A'))
            category = self._clean_text(product.get('category', '-'))
            price = product.get('price', 0.0)
            image_url = product.get('image_url')
            
            # Búsqueda de imagen
            img_path = self._download_image(image_url) if image_url else None
            
            # Simple truncado si el nombre es muy largo
            if len(name) > 40:
                name = name[:37] + "..."
                
            x_start = pdf.get_x()
            y_start = pdf.get_y()
            
            # --- Celda Producto ---
            pdf.cell(100, row_height, "", 1) # Marco
            
            if img_path:
                try:
                    pdf.image(img_path, x=x_start + 2, y=y_start + 1.5, w=image_size, h=image_size)
                    pdf.set_xy(x_start + image_size + 5, y_start)
                    # Alineación vertical manual para el texto
                    pdf.cell(100 - image_size - 5, row_height, name, 0, 0, 'L')
                    os.unlink(img_path)
                except Exception:
                    pdf.set_xy(x_start + 2, y_start)
                    pdf.cell(98, row_height, name, 0, 0, 'L')
            else:
                 pdf.set_xy(x_start + 2, y_start)
                 pdf.cell(98, row_height, name, 0, 0, 'L')

            # Restaurar X para siguientes celdas
            pdf.set_xy(x_start + 100, y_start)
                
            pdf.cell(50, row_height, category, 1, 0, 'C')
            pdf.cell(40, row_height, f"${price:.2f}", 1, 1, 'R')
            
        # --- Footer ---
        pdf.set_y(-20)
        pdf.set_font("Arial", 'I', 8)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 10, self._clean_text("Precios sujetos a cambio sin previo aviso."), align='C')
        
        # Guardar
        file_name = f"catalog_{datetime.now().strftime('%Y%m%d')}.pdf"
        file_path = os.path.join(self.output_dir, file_name)
        pdf.output(file_path)
        
        return os.path.abspath(file_path)
