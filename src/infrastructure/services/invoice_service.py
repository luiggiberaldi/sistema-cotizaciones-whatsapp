import os
from datetime import datetime
from fpdf import FPDF
from typing import Dict, List
from pathlib import Path

class InvoiceService:
    """
    Servicio para generar PDFs de cotizaciones/facturas.
    """
    
    def __init__(self, output_dir: str = "temp_pdfs"):
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
        for item in items:
            product_name = self._clean_text(item['product_name'])
            pdf.cell(90, 8, product_name, 1)
            pdf.cell(30, 8, str(item['quantity']), 1, 0, 'C')
            pdf.cell(35, 8, f"${item['unit_price']:.2f}", 1, 0, 'R')
            pdf.cell(35, 8, f"${item['subtotal']:.2f}", 1, 1, 'R')
            
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

    def generate_delivery_note_pdf(self, quote_data: Dict) -> str:
        """
        Genera una Nota de Entrega (sin precios) para una cotización.
        
        Args:
            quote_data: Diccionario con los datos de la cotización.
            
        Returns:
            Ruta del archivo PDF generado.
        """
        quote_id = quote_data.get('id', 'N/A')
        client_phone = quote_data.get('client_phone', 'N/A')
        items = quote_data.get('items', [])
        date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        pdf = FPDF()
        pdf.add_page()
        
        # --- Cabecera ---
        # Logo placeholder (un rectángulo verde para diferenciar)
        pdf.set_fill_color(46, 204, 113) # Verde
        pdf.rect(10, 10, 40, 20, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 10)
        pdf.set_xy(10, 10)
        pdf.cell(40, 20, "LOGO EMPRESA", align='C')
        
        # Título del Documento
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", 'B', 16)
        pdf.set_xy(60, 10)
        pdf.cell(0, 10, self._clean_text("NOTA DE ENTREGA"), ln=True, align='R')
        
        pdf.set_font("Arial", '', 10)
        pdf.set_xy(60, 20)
        pdf.cell(0, 5, f"Ref. Cotización: #{quote_id}", ln=True, align='R')
        pdf.cell(0, 5, f"Fecha: {date_str}", ln=True, align='R')
        
        pdf.ln(15)
        
        # --- Datos del Cliente ---
        client_name = quote_data.get('client_name') or 'N/A'
        client_dni = quote_data.get('client_dni') or 'N/A'
        client_address = quote_data.get('client_address') or 'N/A'
        
        # Limpiar textos
        client_name = self._clean_text(client_name)
        client_dni = self._clean_text(client_dni)
        client_address = self._clean_text(client_address)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, self._clean_text("Datos de Despacho"), ln=True)
        
        pdf.set_font("Arial", '', 11)
        pdf.cell(30, 6, "Cliente:", 0, 0)
        pdf.cell(0, 6, client_name, ln=True)
        
        pdf.cell(30, 6, "CI/RIF:", 0, 0)
        pdf.cell(0, 6, client_dni, ln=True)
        
        pdf.cell(30, 6, self._clean_text("Dirección:"), 0, 0)
        pdf.multi_cell(0, 6, client_address)
        
        pdf.ln(5)
        
        # --- Tabla de Items (SIN PRECIOS) ---
        # Cabecera de tabla
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 10)
        # Ajustamos anchos para ocupar el espacio de los precios
        pdf.cell(140, 10, "Producto / Descripción", 1, 0, 'C', True)
        pdf.cell(50, 10, "Cantidad", 1, 1, 'C', True)
        
        # Items
        pdf.set_font("Arial", '', 10)
        for item in items:
            product_name = self._clean_text(item['product_name'])
            # Usamos multi_cell para nombres largos si fuera necesario, pero por ahora cell simple
            pdf.cell(140, 8, product_name, 1)
            pdf.cell(50, 8, str(item['quantity']), 1, 0, 'C')
            pdf.ln() # Salto de línea manual al final de la fila
            
        # --- Footer de Recepción ---
        pdf.ln(20)
        
        # Líneas de firma
        y_pos = pdf.get_y()
        pdf.line(20, y_pos, 90, y_pos)
        pdf.line(120, y_pos, 190, y_pos)
        
        pdf.set_font("Arial", '', 9)
        pdf.set_xy(20, y_pos + 2)
        pdf.cell(70, 5, "Despachado por", align='C')
        
        pdf.set_xy(120, y_pos + 2)
        pdf.cell(70, 5, "Recibido Conforme", align='C')
        
        # Guardar archivo
        file_name = f"delivery_{quote_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        file_path = os.path.join(self.output_dir, file_name)
        pdf.output(file_path)
        
        return os.path.abspath(file_path)
