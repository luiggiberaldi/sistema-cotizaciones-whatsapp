import React, { useState } from 'react';
import { CheckSquare, Square } from 'lucide-react';
import QuoteDetailModal from './QuoteDetailModal';

const QuotesTable = ({ quotes, selectedQuotes, onSelectQuote }) => {
    const [selectedQuoteDetail, setSelectedQuoteDetail] = useState(null);
    const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

    const getStatusBadge = (status) => {
        const statusConfig = {
            draft: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Borrador' },
            sent: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Enviado' },
            approved: { bg: 'bg-green-100', text: 'text-green-800', label: 'Aprobado' },
            rejected: { bg: 'bg-red-100', text: 'text-red-800', label: 'Rechazado' },
        };

        const config = statusConfig[status] || statusConfig.draft;

        return (
            <span
                className={`px-3 py-1 rounded-full text-xs font-semibold ${config.bg} ${config.text}`}
            >
                {config.label}
            </span>
        );
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    };

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('es-ES', {
            style: 'currency',
            currency: 'USD',
        }).format(amount);
    };

    const isSelected = (id) => {
        return selectedQuotes.some((quote) => quote.id === id);
    };

    const handleToggleSelect = (e, quote) => {
        e.stopPropagation(); // Stop row click
        const client = {
            id: quote.id, // For compatibility with isSelected
            name: quote.client_name || `Cliente #${quote.id}`,
            phone: quote.client_phone,
            quoteId: quote.id,
            total: quote.total
        };
        onSelectQuote(client);
    };

    const handleRowClick = (quote) => {
        setSelectedQuoteDetail(quote);
        setIsDetailModalOpen(true);
    };

    if (!quotes || quotes.length === 0) {
        return (
            <div className="bg-white rounded-lg shadow p-8 text-center">
                <p className="text-gray-500 text-lg">No hay cotizaciones disponibles</p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Seleccionar
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                # Correlativo
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Cliente
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Teléfono
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Total
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Estado
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Fecha
                            </th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {quotes.map((quote) => (
                            <tr
                                key={quote.id}
                                onClick={() => handleRowClick(quote)}
                                className={`hover:bg-gray-50 transition cursor-pointer ${isSelected(quote.id) ? 'bg-primary-50' : ''
                                    }`}
                            >
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <button
                                        onClick={(e) => handleToggleSelect(e, quote)}
                                        className="text-primary-600 hover:text-primary-800 transition"
                                    >
                                        {isSelected(quote.id) ? (
                                            <CheckSquare size={24} />
                                        ) : (
                                            <Square size={24} />
                                        )}
                                    </button>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="text-sm font-bold text-gray-900">
                                        #{quote.id}
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="text-sm text-gray-900">
                                        {quote.client_name || `Cliente #${quote.id}`}
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="text-sm text-gray-500">
                                        {quote.client_phone}
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="text-sm font-semibold text-gray-900">
                                        {formatCurrency(quote.total)}
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    {getStatusBadge(quote.status)}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {formatDate(quote.created_at)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <QuoteDetailModal
                isOpen={isDetailModalOpen}
                onClose={() => setIsDetailModalOpen(false)}
                quote={selectedQuoteDetail}
            />
        </div>
    );
};

export default QuotesTable;
