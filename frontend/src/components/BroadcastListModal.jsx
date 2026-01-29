import React, { useState, useEffect, useCallback } from 'react';
import { Check, X, Loader2, Search, Filter, Users } from 'lucide-react';
import { customersAPI } from '../services/api';

const normalizePhone = (phone) => {
    if (!phone) return '';
    // Eliminar +, espacios, guiones y cualquier carácter no numérico
    return phone.toString().replace(/[+\s-]/g, '');
};

const BroadcastListModal = ({ isOpen, onClose, onSend, initialSelectedClients = [] }) => {
    // Estados del Mensaje
    const [templateName, setTemplateName] = useState('hello_world');
    const [languageCode, setLanguageCode] = useState('es');
    const [parameters, setParameters] = useState('');
    const [sending, setSending] = useState(false);
    const [results, setResults] = useState(null);

    // Estados de Clientes y Filtros
    const [customers, setCustomers] = useState([]);
    const [loadingCustomers, setLoadingCustomers] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState('');
    const [selectedPhones, setSelectedPhones] = useState(new Set(
        initialSelectedClients.map(c => normalizePhone(c.phone))
    ));

    // Cargar clientes con filtros
    const fetchCustomers = useCallback(async () => {
        setLoadingCustomers(true);
        try {
            const data = await customersAPI.list({
                q: searchQuery,
                status: statusFilter
            });
            setCustomers(data);

            // Si venimos de la tabla con selecciones previas, asegurarnos de que estén en el Set
            if (initialSelectedClients.length > 0 && selectedPhones.size === 0) {
                setSelectedPhones(new Set(initialSelectedClients.map(c => normalizePhone(c.phone))));
            }
        } catch (error) {
            console.error('Error fetching customers:', error);
        } finally {
            setLoadingCustomers(false);
        }
    }, [searchQuery, statusFilter, initialSelectedClients]);

    useEffect(() => {
        if (isOpen) {
            fetchCustomers();
        }
    }, [isOpen, fetchCustomers]);

    // Manejo de Selección
    const toggleCustomer = (phone) => {
        const normalized = normalizePhone(phone);
        const newSelected = new Set(selectedPhones);
        if (newSelected.has(normalized)) {
            newSelected.delete(normalized);
        } else {
            newSelected.add(normalized);
        }
        setSelectedPhones(newSelected);
    };

    const handleSelectAll = (e) => {
        if (e.target.checked) {
            const allPhones = customers.map(c => normalizePhone(c.phone_number));
            setSelectedPhones(new Set([...selectedPhones, ...allPhones]));
        } else {
            // Deseleccionar solo los que están actualmente en la lista filtrada
            const currentPhones = new Set(customers.map(c => normalizePhone(c.phone_number)));
            const newSelected = new Set([...selectedPhones].filter(p => !currentPhones.has(p)));
            setSelectedPhones(newSelected);
        }
    };

    const isAllSelected = customers.length > 0 && customers.every(c => selectedPhones.has(normalizePhone(c.phone_number)));

    const handleSend = async () => {
        if (selectedPhones.size === 0) return;
        setSending(true);
        setResults(null);

        try {
            let params;
            if (templateName === 'payment_reminder') {
                // El backend se encargará de reemplazar {{name}}, {{total}} y {{fecha}}
                params = ['{{name}}', '{{total}}', '{{fecha}}'];
            } else {
                params = parameters
                    .split(',')
                    .map((p) => p.trim())
                    .filter((p) => p);
            }

            // Convertir Set de teléfonos a lista de objetos con name y phone
            // Buscamos en Customers
            // Convertir Set de teléfonos a lista de objetos con name y phone
            const clientsToSend = [...selectedPhones].map(phone => {
                const customer = customers.find(c => normalizePhone(c.phone_number) === phone);
                const initial = initialSelectedClients.find(c => normalizePhone(c.phone) === phone);
                return {
                    name: customer ? customer.full_name : (initial ? initial.name : 'Cliente'),
                    phone: phone,
                    quote_id: initial ? (parseInt(initial.quote_id) || null) : null
                };
            });

            const result = await onSend(clientsToSend, templateName, languageCode, params);
            setResults(result);
        } catch (error) {
            console.error('Error sending broadcast:', error);
            const errorMessage = error.response?.data?.detail || error.message || 'Error desconocido del servidor';
            alert('Error al enviar mensajes: ' + errorMessage);
        } finally {
            setSending(false);
        }
    };

    const handleClose = () => {
        setResults(null);
        setTemplateName('hello_world');
        setLanguageCode('es');
        setParameters('');
        setSelectedPhones(new Set());
        setSearchQuery('');
        setStatusFilter('');
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden">
                {/* Header */}
                <div className="px-6 py-4 border-b flex justify-between items-center bg-white shrink-0">
                    <div className="flex items-center gap-2">
                        <div className="bg-primary-100 p-1.5 sm:p-2 rounded-lg">
                            <Users size={20} className="text-primary-600 sm:w-6 sm:h-6" />
                        </div>
                        <h2 className="text-lg sm:text-2xl font-bold text-gray-800">
                            Difusión 2.0
                        </h2>
                    </div>
                    <button onClick={handleClose} className="text-gray-400 hover:text-gray-600 transition p-2">
                        <X size={24} />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-6 flex flex-col lg:flex-row gap-6">
                    {/* Panel Izquierdo: Filtros y Selección de Clientes */}
                    <div className="flex-1 flex flex-col space-y-4">
                        <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 space-y-4">
                            <div className="flex flex-col sm:flex-row gap-3">
                                {/* Búsqueda */}
                                <div className="relative flex-1">
                                    <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
                                    <input
                                        type="text"
                                        placeholder="Buscar por nombre o celular..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                                    />
                                </div>
                                {/* Filtro Status */}
                                <div className="relative">
                                    <Filter className="absolute left-3 top-2.5 text-gray-400" size={18} />
                                    <select
                                        value={statusFilter}
                                        onChange={(e) => setStatusFilter(e.target.value)}
                                        className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 appearance-none bg-white font-medium text-gray-700"
                                    >
                                        <option value="">Cualquier Estado</option>
                                        <option value="draft">🛒 Solo Borradores</option>
                                        <option value="approved">✅ Solo Aprobados</option>
                                    </select>
                                </div>
                            </div>

                            {/* Select All */}
                            <div className="flex items-center justify-between px-2 text-sm text-gray-600">
                                <label className="flex items-center gap-2 cursor-pointer group">
                                    <input
                                        type="checkbox"
                                        checked={isAllSelected}
                                        onChange={handleSelectAll}
                                        className="w-5 h-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                                    />
                                    <span className="font-semibold group-hover:text-primary-600">Seleccionar Todo ({customers.length})</span>
                                </label>
                                <span className="bg-primary-50 text-primary-700 px-3 py-1 rounded-full font-bold">
                                    {selectedPhones.size} seleccionados
                                </span>
                            </div>
                        </div>

                        {/* Lista de Clientes */}
                        <div className="flex-1 overflow-y-auto border border-gray-200 rounded-xl min-h-[300px]">
                            {loadingCustomers ? (
                                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                                    <Loader2 className="animate-spin mb-2" size={32} />
                                    <p>Cargando clientes...</p>
                                </div>
                            ) : customers.length === 0 ? (
                                <div className="flex flex-col items-center justify-center h-full text-gray-400">
                                    <Users size={48} className="mb-2 opacity-20" />
                                    <p>No se encontraron clientes.</p>
                                </div>
                            ) : (
                                <div className="divide-y divide-gray-100">
                                    {customers.map((customer) => (
                                        <label
                                            key={customer.phone_number}
                                            className={`flex items-center gap-3 px-3 py-2.5 hover:bg-gray-50 cursor-pointer transition ${selectedPhones.has(customer.phone_number) ? 'bg-primary-50/30' : ''}`}
                                        >
                                            <input
                                                type="checkbox"
                                                checked={selectedPhones.has(normalizePhone(customer.phone_number))}
                                                onChange={() => toggleCustomer(customer.phone_number)}
                                                className="w-5 h-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                                            />
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center justify-between">
                                                    <p className="font-bold text-gray-900 leading-tight truncate">{customer.full_name}</p>
                                                </div>
                                                <p className="text-xs sm:text-sm text-gray-500 font-medium">{customer.phone_number}</p>
                                            </div>
                                            {selectedPhones.has(normalizePhone(customer.phone_number)) && (
                                                <Check className="text-primary-600" size={20} />
                                            )}
                                        </label>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Panel Derecho: Configuración de Envío */}
                    <div className="w-full lg:w-80 flex flex-col gap-6 shrink-0">
                        <div className="space-y-4">
                            <h3 className="text-lg font-bold text-gray-800">Mensaje Automático</h3>

                            {/* Template */}
                            <div>
                                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Plantilla de Meta</label>
                                <select
                                    value={templateName}
                                    onChange={(e) => setTemplateName(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 font-medium text-sm"
                                    disabled={sending}
                                >
                                    <option value="hello_world">👋 Hello World</option>
                                    <option value="quote_notification">📄 Notificación Cotización</option>
                                    <option value="payment_reminder">💰 Recordatorio de Pago</option>
                                </select>
                            </div>

                            {/* Parámetros */}
                            <div>
                                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Contenido Extra (Parámetros)</label>
                                {templateName === 'payment_reminder' ? (
                                    <div className="bg-primary-50 p-3 rounded-lg border border-primary-100 space-y-2">
                                        <p className="text-xs text-primary-800 leading-snug">
                                            ✨ Llenado automático de <strong>Nombre</strong> y <strong>Total</strong> activado.
                                        </p>
                                        <input
                                            type="text"
                                            value={parameters}
                                            onChange={(e) => setParameters(e.target.value)}
                                            placeholder="Fecha: ej 'esta tarde'"
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                                            disabled={sending}
                                        />
                                    </div>
                                ) : (
                                    <textarea
                                        value={parameters}
                                        onChange={(e) => setParameters(e.target.value)}
                                        placeholder="Separar por comas..."
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm min-h-[80px]"
                                        disabled={sending}
                                    />
                                )}
                            </div>
                        </div>

                        {/* Resultados */}
                        {results && (
                            <div className="bg-gray-900 text-white rounded-xl p-4 text-sm max-h-[200px] overflow-y-auto no-scrollbar">
                                <h4 className="font-bold mb-2 flex items-center gap-2">
                                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                                    Envíos Finalizados
                                </h4>
                                <div className="space-y-1">
                                    {results.results?.map((res, i) => (
                                        <div key={i} className="py-2 border-b border-gray-800 last:border-0">
                                            <div className="flex justify-between items-center mb-1">
                                                <span className="font-medium text-gray-300">...{res.phone.slice(-4)}</span>
                                                {res.success ? (
                                                    <div className="flex items-center gap-1 text-green-400 text-xs">
                                                        <span>Enviado</span>
                                                        <Check size={14} />
                                                    </div>
                                                ) : (
                                                    <div className="flex items-center gap-1 text-red-400 text-xs">
                                                        <span>Falló</span>
                                                        <X size={14} />
                                                    </div>
                                                )}
                                            </div>
                                            {!res.success && res.error && (
                                                <p className="text-[10px] text-red-500 bg-red-950/30 p-1.5 rounded leading-tight">
                                                    {res.error}
                                                </p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-gray-50 border-t flex flex-col sm:flex-row justify-between items-center gap-4 shrink-0">
                    <p className="text-sm text-gray-500 italic">
                        Los mensajes se enviarán vía la API oficial de WhatsApp Cloud.
                    </p>
                    <div className="flex gap-3 w-full sm:w-auto">
                        <button
                            onClick={handleClose}
                            className="flex-1 sm:flex-none px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition font-bold text-gray-700"
                            disabled={sending}
                        >
                            Cancelar
                        </button>
                        <button
                            onClick={handleSend}
                            disabled={sending || selectedPhones.size === 0}
                            className="flex-1 sm:flex-none px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition font-bold shadow-lg shadow-primary-200 disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {sending ? (
                                <>
                                    <Loader2 className="animate-spin" size={20} />
                                    Procesando...
                                </>
                            ) : (
                                <>Iniciar Difusión ({selectedPhones.size})</>
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BroadcastListModal;

