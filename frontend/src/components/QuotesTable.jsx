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
            quote_id: parseInt(quote.id),
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
        <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto no-scrollbar">
                <table className="min-w-full w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-2 sm:px-6 py-3 text-left text-[10px] sm:text-xs font-medium text-gray-500 uppercase tracking-wider w-8">
                                Sel.
                            </th>
                            <th className="px-2 sm:px-6 py-3 text-left text-[10px] sm:text-xs font-medium text-gray-500 uppercase tracking-wider w-12">
                                # ID
                            </th>
                            <th className="px-2 sm:px-6 py-3 text-left text-[10px] sm:text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Cliente
                            </th>
                            <th className="px-2 sm:px-6 py-3 text-left text-[10px] sm:text-xs font-medium text-gray-500 uppercase tracking-wider hidden md:table-cell">
                                Teléfono
                            </th>
                            <th className="px-2 sm:px-6 py-3 text-left text-[10px] sm:text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Total
                            </th>
                            <th className="px-2 sm:px-6 py-3 text-left text-[10px] sm:text-xs font-medium text-gray-500 uppercase tracking-wider hidden sm:table-cell">
                                Estado
                            </th>
                            <th className="px-2 sm:px-6 py-3 text-left text-[10px] sm:text-xs font-medium text-gray-500 uppercase tracking-wider hidden sm:table-cell">
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
                                <td className="px-2 sm:px-6 py-4 whitespace-nowrap">
                                    <button
                                        onClick={(e) => handleToggleSelect(e, quote)}
                                        className="text-primary-600 hover:text-primary-800 transition"
                                    >
                                        {isSelected(quote.id) ? (
                                            <CheckSquare size={18} className="sm:w-6 sm:h-6" />
                                        ) : (
                                            <Square size={18} className="sm:w-6 sm:h-6" />
                                        )}
                                    </button>
                                </td>
                                <td className="px-2 sm:px-6 py-4 whitespace-nowrap">
                                    <div className="text-[10px] sm:text-sm font-bold text-gray-900">
                                        #{quote.id}
                                    </div>
                                </td>
                                <td className="px-2 sm:px-6 py-4 max-w-[100px] sm:max-w-none truncate sm:whitespace-normal">
                                    <div className="text-[10px] sm:text-sm text-gray-900 font-medium truncate sm:whitespace-normal">
                                        {quote.client_name || `Cliente #${quote.id}`}
                                    </div>
                                </td>
                                <td className="px-2 sm:px-6 py-4 whitespace-nowrap hidden md:table-cell">
                                    <div className="text-xs sm:text-sm text-gray-500">
                                        {quote.client_phone}
                                    </div>
                                </td>
                                <td className="px-2 sm:px-6 py-4 whitespace-nowrap">
                                    <div className="text-xs sm:text-sm font-bold text-gray-900">
                                        {formatCurrency(quote.total)}
                                    </div>
                                </td>
                                <td className="px-2 sm:px-6 py-4 whitespace-nowrap hidden sm:table-cell">
                                    {getStatusBadge(quote.status)}
                                </td>
                                <td className="px-2 sm:px-6 py-4 whitespace-nowrap text-[10px] sm:text-sm text-gray-500 hidden sm:table-cell">
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
