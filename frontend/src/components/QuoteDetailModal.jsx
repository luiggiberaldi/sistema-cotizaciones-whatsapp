import React, { useState } from 'react';
import { X, FileText, Download, User, MapPin, Phone, CreditCard } from 'lucide-react';
import { quotesAPI } from '../services/api';

const QuoteDetailModal = ({ isOpen, onClose, quote }) => {
    const [generatingPdf, setGeneratingPdf] = useState(false);

    if (!isOpen || !quote) return null;

    const handleGeneratePdf = async () => {
        try {
            setGeneratingPdf(true);
            const blob = await quotesAPI.generatePdf(quote.id);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Cotizacion_${quote.id}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error("Error generating PDF:", error);
            alert("Error al generar el PDF. Por favor intente de nuevo.");
        } finally {
            setGeneratingPdf(false);
        }
    };

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('es-ES', {
            style: 'currency',
            currency: 'USD',
        }).format(amount);
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto relative">
                {/* Header */}
                <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center z-10">
                    <div className="flex items-center gap-2">
                        <FileText className="text-primary-600" size={24} />
                        <h2 className="text-xl font-bold text-gray-800">
                            Detalle de Cotización #{quote.id}
                        </h2>
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold uppercase ml-2 
                            ${quote.status === 'bg-green-100 text-green-800' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                            {quote.status}
                        </span>
                    </div>
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
                        <X size={24} />
                    </button>
                </div>

                <div className="p-6 space-y-8">
                    {/* Client Info */}
                    <div className="bg-gray-50 rounded-lg p-5 border border-gray-100">
                        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4 flex items-center gap-2">
                            <User size={16} /> Datos del Cliente
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <p className="text-xs text-gray-500 mb-1">Cliente</p>
                                <p className="font-medium text-gray-900 text-lg">{quote.client_name || 'No registrado'}</p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-500 mb-1">CI / RIF</p>
                                <p className="font-medium text-gray-900">{quote.client_dni || 'No registrado'}</p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-500 mb-1 flex items-center gap-1"><Phone size={12} /> Teléfono</p>
                                <p className="font-medium text-gray-900">{quote.client_phone}</p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-500 mb-1 flex items-center gap-1"><MapPin size={12} /> Dirección</p>
                                <p className="font-medium text-gray-900 truncate" title={quote.client_address}>
                                    {quote.client_address || 'Sin dirección'}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Items Table */}
                    <div>
                        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                            Items de la Cotización
                        </h3>
                        <div className="border rounded-lg overflow-hidden">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Producto</th>
                                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Cant.</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Precio Unit.</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Subtotal</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {quote.items?.map((item, idx) => (
                                        <tr key={idx}>
                                            <td className="px-4 py-3 text-sm text-gray-900">{item.product_name}</td>
                                            <td className="px-4 py-3 text-sm text-gray-900 text-center">{item.quantity}</td>
                                            <td className="px-4 py-3 text-sm text-gray-500 text-right">{formatCurrency(item.unit_price)}</td>
                                            <td className="px-4 py-3 text-sm font-medium text-gray-900 text-right">{formatCurrency(item.subtotal)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Total & Actions */}
                    <div className="flex flex-col md:flex-row justify-between items-end gap-4 border-t pt-6">
                        <button
                            onClick={handleGeneratePdf}
                            disabled={generatingPdf}
                            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors shadow-sm"
                        >
                            {generatingPdf ? (
                                <div className="w-5 h-5 border-2 border-gray-600 border-t-transparent rounded-full animate-spin"></div>
                            ) : (
                                <Download size={18} />
                            )}
                            Generar PDF de Nuevo
                        </button>

                        <div className="bg-gray-900 text-white px-8 py-4 rounded-lg shadow-lg text-right">
                            <p className="text-xs text-gray-400 uppercase mb-1">Monto Total</p>
                            <p className="text-3xl font-bold">{formatCurrency(quote.total)}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default QuoteDetailModal;
