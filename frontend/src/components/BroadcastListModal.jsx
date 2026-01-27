import React from 'react';
import { Check, X, Loader2 } from 'lucide-react';

const BroadcastListModal = ({ isOpen, onClose, selectedClients, onSend }) => {
    const [templateName, setTemplateName] = React.useState('hello_world');
    const [languageCode, setLanguageCode] = React.useState('es');
    const [parameters, setParameters] = React.useState('');
    const [sending, setSending] = React.useState(false);
    const [results, setResults] = React.useState(null);

    const handleSend = async () => {
        setSending(true);
        setResults(null);

        try {
            const params = parameters
                .split(',')
                .map((p) => p.trim())
                .filter((p) => p);

            const result = await onSend(selectedClients, templateName, languageCode, params);
            setResults(result);
        } catch (error) {
            console.error('Error sending broadcast:', error);
            alert('Error al enviar mensajes: ' + error.message);
        } finally {
            setSending(false);
        }
    };

    const handleClose = () => {
        setResults(null);
        setTemplateName('hello_world');
        setLanguageCode('es');
        setParameters('');
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
                    <h2 className="text-2xl font-bold text-gray-800">
                        📢 Lista de Difusión
                    </h2>
                    <button
                        onClick={handleClose}
                        className="text-gray-500 hover:text-gray-700 transition"
                    >
                        <X size={24} />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-6">
                    {/* Clientes seleccionados */}
                    <div>
                        <h3 className="text-lg font-semibold text-gray-700 mb-3">
                            Clientes Seleccionados ({selectedClients.length})
                        </h3>
                        <div className="bg-gray-50 rounded-lg p-4 max-h-40 overflow-y-auto">
                            {selectedClients.map((client, index) => (
                                <div
                                    key={index}
                                    className="flex items-center justify-between py-2 border-b last:border-b-0"
                                >
                                    <div>
                                        <p className="font-medium text-gray-800">{client.name}</p>
                                        <p className="text-sm text-gray-500">{client.phone}</p>
                                    </div>
                                    <Check className="text-green-500" size={20} />
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Configuración del template */}
                    <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-700">
                            Configuración del Mensaje
                        </h3>

                        {/* Template Name */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Nombre del Template
                            </label>
                            <select
                                value={templateName}
                                onChange={(e) => setTemplateName(e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                                disabled={sending}
                            >
                                <option value="hello_world">Hello World</option>
                                <option value="quote_notification">Notificación de Cotización</option>
                                <option value="payment_reminder">Recordatorio de Pago</option>
                            </select>
                            <p className="text-xs text-gray-500 mt-1">
                                Solo templates aprobados por Meta
                            </p>
                        </div>

                        {/* Language Code */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Idioma
                            </label>
                            <select
                                value={languageCode}
                                onChange={(e) => setLanguageCode(e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                                disabled={sending}
                            >
                                <option value="es">Español (es)</option>
                                <option value="en">English (en)</option>
                                <option value="pt">Português (pt)</option>
                            </select>
                        </div>

                        {/* Parameters */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Parámetros (separados por coma)
                            </label>
                            <input
                                type="text"
                                value={parameters}
                                onChange={(e) => setParameters(e.target.value)}
                                placeholder="Ej: Juan, $100.00"
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                                disabled={sending}
                            />
                            <p className="text-xs text-gray-500 mt-1">
                                Opcional: valores para variables del template
                            </p>
                        </div>
                    </div>

                    {/* Resultados */}
                    {results && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <h4 className="font-semibold text-blue-900 mb-2">
                                Resultados del Envío
                            </h4>
                            <div className="space-y-2">
                                {results.results?.map((result, index) => (
                                    <div
                                        key={index}
                                        className={`flex items-center justify-between p-2 rounded ${result.success
                                                ? 'bg-green-100 text-green-800'
                                                : 'bg-red-100 text-red-800'
                                            }`}
                                    >
                                        <span className="text-sm">{result.phone}</span>
                                        {result.success ? (
                                            <Check size={16} />
                                        ) : (
                                            <X size={16} />
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="sticky bottom-0 bg-gray-50 px-6 py-4 flex justify-end gap-3 border-t">
                    <button
                        onClick={handleClose}
                        className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition font-medium"
                        disabled={sending}
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={handleSend}
                        disabled={sending || selectedClients.length === 0}
                        className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {sending ? (
                            <>
                                <Loader2 className="animate-spin" size={20} />
                                Enviando...
                            </>
                        ) : (
                            <>Enviar Mensajes ({selectedClients.length})</>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default BroadcastListModal;
